# tfm_cic
TFM CIC ENDESA during 2020-2021

			THESE ARE INSTRUCTIONS TO RUN THE SCRIPT app_Malaga_Visual_Tool.

In this file, I explain how to properly set the environment recquired in terms of librairies and dependancies then
observe the html in output.

1. Prepare the following structure:
	- app_Malaga_Visual_Tool.py and environment.yml file in the same folder (dir: ~/CODE/.)
	- assets folder on the same level, with png and css files
	- LVSM_Def.xlsx and Listafo_Trafos.xlsx on a different folder called DATA, one level (dir: ~/DATA/.)

2. Open the VS Code interface and on a new terminal, after locating in the CODE folder:
	- Execute: conda env create -f environment.yml

3. Activate the environment
	- Execute: conda activate tfm_cic

4. Run the script, then this message should appear in the terminal below:
	Dash is running on http://127.0.0.1:8050/

 * Serving Flask app 'app_Malaga_Visual_Tool' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.

5. Then after a few minutes, enter in the local url http://127.0.0.1:8050/

6. Use the tool as desired


Notes:  To remove the environment once used, delete by executing: conda remove --name myenv --all
	Verify it was successfully deleted, try conda info --envs and check if it still exists

	To prepare a new environment.yml: conda env export > environment.yml
