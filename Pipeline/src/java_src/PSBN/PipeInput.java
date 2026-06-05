package PSBN;

public class PipeInput {
    public final Integer dim;
    public final String lp_enumeratorFile;
    public final String setup_btreeFolder;
    public final Integer nSolutions;
    public final String output_path;

    public PipeInput(Integer dim, String lp_enumeratorFile, String setup_btreeFolder, Integer nSolutions, String output_path) {
        this.dim = dim;
        this.lp_enumeratorFile = lp_enumeratorFile;
        this.setup_btreeFolder = setup_btreeFolder;
        this.nSolutions = nSolutions;
        this.output_path = output_path;
    }
}
