import subprocess
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


if __name__=="__main__":

    df = pd.read_csv("transition_function_3d_output.csv")
    d = df.shape[1]
    frequencies = np.zeros(len(df),dtype = int)

    for i in range(len(df)):
        constant = [f"-c f{j}={df[f'f_{j}'][i]}" for j in range(d)]
        result = subprocess.run(
            ["clingcon", "0", "count_frequency.lp", "--parallel", "12"] + constant,
            capture_output=True, text=True
        )

        result_iterator = reversed(result.stdout.splitlines())

        while (line := next(result_iterator, None)) is not None:
            print(line)
            if line.startswith("Models"):
                frequencies[i] = int(re.search(r'\d+', line).group(0))
                print(i,frequencies[i])
                break
    
    
    plt.semilogy(range(1,len(df)+1),sorted(frequencies,reverse=True))
    plt.show()
