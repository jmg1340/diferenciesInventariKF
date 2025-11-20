import pandas as pd

def debug_kardex_file(file_path):
    """
    Lee una hoja del fichero Kardex, salta las cabeceras y guarda las primeras
    filas en un fichero de texto para poder analizar su estructura.
    """
    output_file = 'debug_output.txt'
    try:
        xls = pd.ExcelFile(file_path)
        sheet_names = [name for name in xls.sheet_names if name.startswith('stockHuecos')]

        if not sheet_names:
            with open(output_file, 'w') as f:
                f.write("Error: No se encontraron hojas con el nombre 'stockHuecos'.")
            return

        # Analizamos solo la primera hoja encontrada
        sheet_to_debug = sheet_names[0]
        
        # Leemos las primeras 250 filas despues de la cabecera para tener una buena muestra
        df = pd.read_excel(xls, sheet_name=sheet_to_debug, skiprows=12, header=None, nrows=250)

        # Guardamos la representacion en string del DataFrame a un fichero
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"--- Analizando las primeras 250 filas de la hoja: {sheet_to_debug} ---\n")
            f.write("--- (Saltando las primeras 12 filas del fichero original) ---\n\n")
            f.write(df.to_string())
        
        print(f"Fichero de depuración '{output_file}' creado. Por favor, muestra su contenido.")

    except Exception as e:
        with open(output_file, 'w') as f:
            f.write(f"Ocurrió un error al procesar el fichero: {e}")
        print(f"Fichero de depuración '{output_file}' creado con un mensaje de error.")

if __name__ == "__main__":
    kardex_file_path = 'dadesCarregades/STK-Cen-ContingenciaArticulos-20251114_070021.xls'
    debug_kardex_file(kardex_file_path)
