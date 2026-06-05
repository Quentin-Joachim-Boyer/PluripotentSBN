/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package PSBN.Processors;

import com.gitlab.jpp.Processor;
import com.gitlab.jpp.parameters.*;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author segretar
 * @author boyerque
 */
public class DataStringLineCollectorProcessor implements Processor<String, Void> {

	private final StringParameter path;
	private final StringParameter filename;

	private BufferedWriter bw;

	public DataStringLineCollectorProcessor(StringParameter path,
			StringParameter filename) {

		this.path = path;
		this.filename = filename;
	}

	@Override
	public void reset() {
		try {
			this.bw = new BufferedWriter(new FileWriter(new File(
					this.path.getText() + System.getProperty("file.separator") + this.filename.getText())));
		} catch (IOException ex) {
			Logger.getLogger(DataStringLineCollectorProcessor.class.getName()).log(
					Level.SEVERE, null, ex);
		}
	}

	@Override
	public synchronized Void process(String input) {
		// System.out.println(input);
		try {
			bw.write(input);
			bw.newLine();
			// fw.flush();
		} catch (IOException ex) {
			Logger.getLogger(DataStringLineCollectorProcessor.class.getName()).log(
					Level.SEVERE, null, ex);
		}
		return null;
	}

	public void flush() {
		try {
			this.bw.flush();
		} catch (IOException ex) {
			Logger.getLogger(DataStringLineCollectorProcessor.class.getName()).log(
					Level.SEVERE, null, ex);
		}
	}
}
