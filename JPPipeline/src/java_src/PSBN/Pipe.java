package PSBN;

import PSBN.Processors.DataStringLineCollectorProcessor;
import PSBN.Processors.Decomposer;
import PSBN.Processors.EnumeratorPSBN;
import PSBN.Processors.EnumeratorPSBNFull;
import PSBN.Processors.Minimizer;
import PSBN.Processors.Statifier;
import PSBN.util.DecompVector;
import PSBN.util.EnumerationResult;
import PSBN.util.RealizableSBFs;
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
    // monolithique fait sauter le garde-fou et le vecteur est subdivise par SBF.
    private static final int SUBDIVISION_THRESHOLD = 10000;

    private final IntegerParameter dim;
    private final StringParameter lp_enumeratorFile;
    private final StringParameter setup_btreeFolder;
    private final IntegerParameter nSolutions;
    private final StringParameter outputFileName;
    private final StringParameter outputFilePath;


    private final Job<Integer, ArrayList<DecompVector>> DecompositionJob;
    private final Job<DecompVector, EnumerationResult> EnumerationJob;
    private final Job<Pair<DecompVector, Integer>, Void> SubdividedEnumerationJob;
    private final Job<SBNP, SBNP> MinimizationJob;
    private final Job<SBNP,String> StatificationJob;

    // Conserve pour injecter le sink de streaming une fois MinimizationJob construit.
    private final EnumeratorPSBN subdividedEnumerator;

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

        
        this.DecompositionJob = new Job.JobBuilder<Integer, ArrayList<DecompVector>>(this, new Decomposer())
                .setTaskSubmitter(new TaskHolder(this.startSignal))
                .setOutputHandler(new OutputHandler<ArrayList<DecompVector>>() {
                    @Override
                    public void handle(ArrayList<DecompVector> processorOutput) {
                        for (DecompVector dv : processorOutput) {
                            EnumerationJob.buildNewTask(dv);
                        }
                    }
                })
                .setEndOfJobAction(OneTimeAction.printActionFactory("Decomposition Job terminated"))
                .build();
        // Enumeration monolithique avec garde-fou. Selon le resultat, l'output
        // handler route soit directement vers la minimisation (cas majoritaire),
        // soit vers l'enumeration subdivisee par SBF (vecteurs lourds).
        this.EnumerationJob = new Job.JobBuilder<DecompVector, EnumerationResult>(this, new EnumeratorPSBNFull(this.lp_enumeratorFile,this.setup_btreeFolder,this.nSolutions,SUBDIVISION_THRESHOLD), this.DecompositionJob)
                .setOutputHandler(new OutputHandler<EnumerationResult>() {
                    @Override
                    public void handle(EnumerationResult result) {
                        if (!result.overflowed) {
                            for (SBNP sbn : result.solutions) {
                                MinimizationJob.buildNewTask(sbn);
                            }
                        } else {
                            // Vecteur trop gros : on subdivise par SBF du noeud 1,
                            // en ne retenant que les SBF realisables par un vecteur
                            // de poids entier (les autres seraient de toute facon UNSAT).
                            int n = result.dv.getDimension();
                            for (int sbf : RealizableSBFs.forDimension(n)) {
                                SubdividedEnumerationJob.buildNewTask(new Pair<>(result.dv, sbf));
                            }
                        }
                    }
                })
                .setMaximumParallelTasks(10)
                .setEndOfJobAction(OneTimeAction.printActionFactory("Enumeration Job terminated"))
                .build();
        // L'enumeration subdivisee streame chaque solution directement vers la
        // minimisation (via le sink injecte plus bas), sans accumuler : son output
        // est Void et elle n'a pas d'output handler.
        this.subdividedEnumerator = new EnumeratorPSBN(this.lp_enumeratorFile,this.setup_btreeFolder,this.nSolutions);
        this.SubdividedEnumerationJob = new Job.JobBuilder<Pair<DecompVector, Integer>, Void>(this, this.subdividedEnumerator, this.EnumerationJob)
                .setEndOfJobAction(OneTimeAction.printActionFactory("Subdivided Enumeration Job terminated"))
                .setMaximumParallelTasks(10)
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
        csv_header.append(",AtrSize,GenotypeCount,R_P_std,R_P_mean,E_P");
        this.dataCollector.process(csv_header.toString());
    }

    @Override
    protected void initialTasks() {
        System.out.println(String.format("The pipeline is starting to bring itself to the idea of working on the dimension d=%d BOUHH !!!",input.dim));
        this.DecompositionJob.buildNewTask(input.dim);
    }
    @Override
    protected void after() {
        super.after();
        this.dataCollector.flush();
        System.out.println("Done");
    }
    
}