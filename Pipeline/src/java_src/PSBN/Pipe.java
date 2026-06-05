package PSBN;

import PSBN.Processors.DataStringLineCollectorProcessor;
import PSBN.Processors.Decomposer;
import PSBN.Processors.Enumerator_PSBN;
import PSBN.Processors.Enumerator_PSBN_full;
import PSBN.Processors.Minimizer;
import PSBN.Processors.Statifier;
import PSBN.util.Decomp_vector;
import PSBN.util.EnumerationResult;
import PSBN.util.SBNP;
import java.util.ArrayList;

import com.gitlab.jpp.Job;
import com.gitlab.jpp.OneTimeAction;
import com.gitlab.jpp.OutputHandler;
import com.gitlab.jpp.Pipeline;
import com.gitlab.jpp.TaskHolder;
import com.gitlab.jpp.parameters.IntegerParameter;
import com.gitlab.jpp.parameters.Pair;
import com.gitlab.jpp.parameters.StringParameter;

/**
 * @author BOYER
 */


public class Pipe extends Pipeline<PipeInput,Void> {

    // Au dela de ce nombre de solutions pour un vecteur, l'enumeration
    // monolithique fait sauter le garde-fou et le vecteur est subdivise par masque.
    private static final int SUBDIVISION_THRESHOLD = 1000;

    private final IntegerParameter dim;
    private final StringParameter lp_enumeratorFile;
    private final StringParameter setup_btreeFolder;
    private final IntegerParameter nSolutions;
    private final StringParameter outputFileName;
    private final StringParameter outputFilePath;


    private final Job<Integer, ArrayList<Decomp_vector>> DecompositionJob;
    private final Job<Decomp_vector, EnumerationResult> EnumerationJob;
    private final Job<Pair<Decomp_vector, Integer>, Void> SubdividedEnumerationJob;
    private final Job<SBNP, SBNP> MinimizationJob;
    private final Job<SBNP,String> StatificationJob;

    // Conserve pour injecter le sink de streaming une fois MinimizationJob construit.
    private final Enumerator_PSBN subdividedEnumerator;

    private final DataStringLineCollectorProcessor dataCollector;

    @SuppressWarnings("unchecked")    
    public Pipe() {
        super(Runtime.getRuntime().availableProcessors());

        this.dim = new IntegerParameter(0);
        this.lp_enumeratorFile = new StringParameter("");
        this.setup_btreeFolder = new StringParameter("");
        this.nSolutions = new IntegerParameter(0);
        this.outputFileName = new StringParameter("");
        this.outputFilePath = new StringParameter("");;

        
        this.DecompositionJob = new Job.JobBuilder<Integer, ArrayList<Decomp_vector>>(this, new Decomposer())
                .setTaskSubmitter(new TaskHolder(this.startSignal))
                .setOutputHandler(new OutputHandler<ArrayList<Decomp_vector>>() {
                    @Override
                    public void handle(ArrayList<Decomp_vector> processorOutput) {
                        for (Decomp_vector dv : processorOutput) {
                            EnumerationJob.buildNewTask(dv);
                        }
                    }
                })
                .setEndOfJobAction(OneTimeAction.printActionFactory("Decomposition Job terminated"))
                .build();
        // Enumeration monolithique avec garde-fou. Selon le resultat, l'output
        // handler route soit directement vers la minimisation (cas majoritaire),
        // soit vers l'enumeration subdivisee par masque (vecteurs lourds).
        this.EnumerationJob = new Job.JobBuilder<Decomp_vector, EnumerationResult>(this, new Enumerator_PSBN_full(this.lp_enumeratorFile,this.setup_btreeFolder,this.nSolutions,SUBDIVISION_THRESHOLD), this.DecompositionJob)
                .setOutputHandler(new OutputHandler<EnumerationResult>() {
                    @Override
                    public void handle(EnumerationResult result) {
                        if (!result.overflowed) {
                            for (SBNP sbn : result.solutions) {
                                MinimizationJob.buildNewTask(sbn);
                            }
                        } else {
                            // Vecteur trop gros : on subdivise par masque du noeud 1.
                            int n = result.dv.getDimension();
                            long numMasks = 1L << (1 << n); // 2^(2^n)
                            for (long mask = 0; mask < numMasks; mask++) {
                                SubdividedEnumerationJob.buildNewTask(new Pair<>(result.dv, (int) mask));
                            }
                        }
                    }
                })
                .setEndOfJobAction(OneTimeAction.printActionFactory("Enumeration Job terminated"))
                .build();
        // L'enumeration subdivisee streame chaque solution directement vers la
        // minimisation (via le sink injecte plus bas), sans accumuler : son output
        // est Void et elle n'a pas d'output handler.
        this.subdividedEnumerator = new Enumerator_PSBN(this.lp_enumeratorFile,this.setup_btreeFolder,this.nSolutions);
        this.SubdividedEnumerationJob = new Job.JobBuilder<Pair<Decomp_vector, Integer>, Void>(this, this.subdividedEnumerator, this.EnumerationJob)
                .setEndOfJobAction(OneTimeAction.printActionFactory("Subdivided Enumeration Job terminated"))
                .build();
        this.MinimizationJob = new Job.JobBuilder<SBNP,SBNP>(this, new Minimizer(), this.EnumerationJob, this.SubdividedEnumerationJob)
                .setOutputHandler(new OutputHandler<SBNP>() {
                    @Override
                    public void handle(SBNP processorOutput) {
                        StatificationJob.buildNewTask(processorOutput);
                    }
                })
                .build();
        // Le sink de streaming pousse chaque SBNP comme une tache de minimisation.
        // Sur (cf. analyse JPP) : appele depuis process() d'une tache subdivisee
        // encore en cours, donc MinimizationJob n'est jamais prematurement termine.
        this.subdividedEnumerator.setSink(sbn -> MinimizationJob.buildNewTask(sbn));
        this.StatificationJob = new Job.JobBuilder<SBNP,String>(this, new Statifier(), this.MinimizationJob)
                .setOutputHandler(new OutputHandler<String>() {
                    @Override
                    public void handle(String processorOutput) {
                        dataCollector.process(processorOutput);
                    }
                })
                .setEndOfJobAction(OneTimeAction.printActionFactory("Statification Job terminated"))
                .build();

        this.dataCollector = new DataStringLineCollectorProcessor(
            this.outputFilePath, 
            this.outputFileName
        );   
    }

    @Override
    protected void reset() {
        this.dim.setValue(this.input.dim);
        this.lp_enumeratorFile.setText(this.input.lp_enumeratorFile);
        this.setup_btreeFolder.setText(this.input.setup_btreeFolder);
        this.nSolutions.setValue(this.input.nSolutions);
        String SBN_type = java.nio.file.Paths.get(lp_enumeratorFile.getText()).getFileName().toString().replaceAll("\\.lp$", "");
        this.outputFileName.setText(Integer.toString(this.dim.getValue()) + "d_" + SBN_type + "_output.csv");
        this.outputFilePath.setText(this.input.output_path);
        this.dataCollector.reset();
        int n = this.dim.getValue();
        StringBuilder csv_header = new StringBuilder();
        for (int i = 0; i <= n; i++)
            csv_header.append("v_").append(n - i).append(",");
        for (int j = 1; j <= n; j++)
            csv_header.append("f_").append(j).append(",");
        for (int i = 1; i <= n; i++)
            for (int j = 1; j <= n; j++) {
                csv_header.append("\"w_").append(i).append(",").append(j).append("\"");
                if (i < n || j < n) csv_header.append(",");
            }
        this.dataCollector.process(csv_header.toString());
    }

    @Override
    protected void initialTasks() {
        System.out.println("BOUH !!!");
        this.DecompositionJob.buildNewTask(input.dim);
    }
    @Override
    protected void after() {
        super.after();
        this.dataCollector.flush();
        System.out.println("Done");
    }
    
}