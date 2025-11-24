import pandas as pd

def procesar_farhos(file_path):
    """
    Procesa el fichero de inventario de Farhos.
    Lee un fichero Excel, lo limpia y estandariza las columnas.

    Args:
        file_path (str): Ruta al fichero Excel de Farhos.

    Returns:
        pandas.DataFrame: DataFrame con las columnas ['codigo', 'descripcion', 'stock'].
                           Retorna None si hay un error.
    """
    try:
        # Leemos el fichero de Excel, saltando la primera fila que puede contener un titulo.
        df = pd.read_excel(file_path, skiprows=1)

        # --- Estandarización de Nombres de Columna ---
        # Define un mapa para renombrar las columnas del fichero original a nombres estandar.
        # ESTA SECCIÓN ES CRÍTICA Y DEBE AJUSTARSE AL FORMATO DEL FICHERO REAL.
        column_map = {
            'Cód.Esp': 'codigo',
            'Especialidad': 'descripcion',
            'Unidades': 'stock'
        }
        
        # Aplica el renombrado de columnas.
        df.rename(columns=column_map, inplace=True)

        # --- Validación y Limpieza de Datos ---

        # Verifica que las columnas esenciales ('codigo', 'stock') existan despues de renombrar.
        if 'codigo' not in df.columns or 'stock' not in df.columns:
            raise ValueError("No se encontraron las columnas de 'codigo' o 'stock' en el fichero de Farhos.")

        # Si no hay columna de 'descripcion', se crea una con un valor por defecto.
        if 'descripcion' not in df.columns:
            df['descripcion'] = 'Sin descripción'

        # Selecciona solo las columnas de interes para el resto del proceso.
        df = df[['codigo', 'descripcion', 'stock']]

        # Convierte la columna 'codigo' a tipo string para evitar problemas con formatos numericos.
        df['codigo'] = df['codigo'].astype(str)
        print(df.head())
        
        # Treu el decimal '.0'
        df['codigo'] = df['codigo'].str.replace(r"\.0$", "", regex=True)
        print("\n-----------\n", df.head())

        # Elimina cualquier fila que no tenga un valor en 'codigo' o 'stock'.
        df.dropna(subset=['codigo', 'stock'], inplace=True)
        
        # Asegura que la columna 'stock' sea de tipo numerico, convirtiendo errores en 0.
        df['stock'] = pd.to_numeric(df['stock'], errors='coerce').fillna(0)
        
        # Sembla que les dades del stock son float i tenen el decimal '.0'. Convertim a int per treure decimal
        df['stock'] = df['stock'].astype("Int64")

        # --- Agrupación ---
        # Agrupa las filas por 'codigo' y 'descripcion' y suma el 'stock'.
        # Esto consolida los productos duplicados en una sola entrada.
        df_agrupado = df.groupby(['codigo', 'descripcion']).agg({'stock': 'sum'}).reset_index()

        return df_agrupado

    except Exception as e:
        # Si ocurre cualquier error durante el proceso, se imprime y se retorna None.
        print(f"Error al procesar el fichero de Farhos: {e}")
        return None

def procesar_kardex(file_path):
    """
    Procesa el fichero de inventario de Kardex, que puede tener multiples hojas.
    Lee los datos, combina columnas para formar los campos deseados y los limpia.

    Args:
        file_path (str): Ruta al fichero Excel de Kardex.

    Returns:
        pandas.DataFrame: DataFrame con las columnas ['codigo', 'descripcion', 'stock'].
                           Retorna None si hay un error.
    """
    try:
        # Abre el fichero Excel para poder acceder a sus hojas.
        xls = pd.ExcelFile(file_path)
        all_sheets_df = [] # Lista para almacenar los DataFrames de cada hoja.

        # Filtra y obtiene los nombres de las hojas que nos interesan (las que empiezan con 'stockHuecos').
        sheet_names = [name for name in xls.sheet_names if name.startswith('stockHuecos')]

        # Itera sobre cada una de las hojas encontradas.
        for sheet_name in sheet_names:
            # Lee la hoja actual, saltando las primeras 12 filas de cabecera.
            # 'header=None' indica que el fichero no tiene una fila de encabezado que pandas deba usar.
            df_sheet = pd.read_excel(xls, sheet_name=sheet_name, header=12)   # , skiprows=11
            
            # --- Combinacion de Columnas (Lógica actual) ---
            # ESTA LÓGICA ES COMPLEJA Y PUEDE NECESITAR AJUSTES SEGÚN LA ESTRUCTURA EXACTA DEL FICHERO.
 
            column_map = {
                'Cod.': 'codigo',
                'Descripción': 'descripcion',
                'Stock': 'stock'
            }
        
            # Aplica el renombrado de columnas.
            df_sheet.rename(columns=column_map, inplace=True)
           

            # filtrem les files que el Stock tingui alguna dada y que aquesta no sigui "Stock"
            filtre = flt = (df_sheet["stock"].notna()) & (df_sheet["stock"] != "Stock")
            df_sheet = df_sheet[filtre]            


            '''
            # 1. Creación de 'descripcion': Combina el contenido de las columnas 3 y 4.
            col_3 = df_sheet.get(3, pd.Series(dtype=str)).fillna('').astype(str)
            col_4 = df_sheet.get(4, pd.Series(dtype=str)).fillna('').astype(str)
            df_sheet['descripcion'] = (col_3 + col_4).str.strip()

            # 2. Creación de 'stock': Combina el contenido de las columnas 5 y 6.
            col_5 = df_sheet.get(5, pd.Series(dtype=str)).fillna('').astype(str)
            col_6 = df_sheet.get(6, pd.Series(dtype=str)).fillna('').astype(str)
            df_sheet['stock'] = (col_5 + col_6).str.strip()

            # 3. Creación de 'codigo': Suma los valores numéricos de las columnas 1 y 2.
            stock_1 = pd.to_numeric(df_sheet.get(1), errors='coerce').fillna(0)
            stock_2 = pd.to_numeric(df_sheet.get(2), errors='coerce').fillna(0)
            df_sheet['codigo'] = stock_1 + stock_2
            '''
            
            # --- Limpieza y Filtro ---
            
            # Reemplaza los códigos vacíos con NaN (Not a Number) para poder eliminarlos.
            df_sheet['codigo'] = df_sheet['codigo'].replace('', pd.NA)
            df_sheet.dropna(subset=['codigo'], inplace=True)

            # Si la hoja queda vacía después del filtro, se salta a la siguiente.
            if df_sheet.empty:
                continue

            # Selecciona solo las columnas finales que hemos creado.
            final_cols = df_sheet[['codigo', 'descripcion', 'stock']]
            all_sheets_df.append(final_cols)

        # Si ninguna hoja produjo datos válidos, se lanza un error.
        if not all_sheets_df:
            raise ValueError("No se pudo leer ninguna hoja de datos valida en el fichero de Kardex.")

        # Concatena todos los DataFrames de las hojas en uno solo.
        df_total = pd.concat(all_sheets_df, ignore_index=True)

        # --- Limpieza Final y Agrupación ---

        # Asegura que el stock sea numérico y los códigos y descripciones sean strings.
        df_total['stock'] = pd.to_numeric(df_total['stock'], errors='coerce').fillna(0)
        df_total['codigo'] = df_total['codigo'].astype(str)
        df_total['descripcion'] = df_total['descripcion'].replace('', 'Sin descripción')

        # Sembla que les dades del stock son float i tenen el decimal '.0'. Convertim a int per treure decimal
        df_total['stock'] = df_total['stock'].astype("Int64")


        # Agrupa por 'codigo' y 'descripcion' para consolidar productos duplicados.
        df_agrupado = df_total.groupby(['codigo', 'descripcion']).agg({'stock': 'sum'}).reset_index()

        return df_agrupado

    except Exception as e:
        # Si ocurre cualquier error, se imprime y se retorna None.
        print(f"Error al procesar el fichero de Kardex: {e}")
        return None

def comparar_inventarios(df_farhos, df_kardex):
    """
    Compara dos DataFrames de inventario (Farhos y Kardex) y calcula las diferencias de stock.

    Args:
        df_farhos (pandas.DataFrame): DataFrame de Farhos.
        df_kardex (pandas.DataFrame): DataFrame de Kardex.

    Returns:
        pandas.DataFrame: DataFrame con la comparativa, incluyendo una columna 'Diferencia'.
    """
    if df_farhos is None or df_kardex is None:
        return None

    # --- Fusión de Datos ---
    # Se realiza un 'outer merge' para asegurar que todos los productos de ambos
    # inventarios se incluyan en el resultado, incluso si no existen en el otro.
    df_comparativa = pd.merge(
        df_farhos, 
        df_kardex, 
        on='codigo', 
        how='outer', 
        suffixes=('_farhos', '_kardex') # Sufijos para diferenciar columnas con el mismo nombre (ej. 'stock_farhos').
    )

    # --- Limpieza Post-Fusión ---
    # Determina si un producto es externo (si no tiene stock en Kardex después de la fusión)
    df_comparativa['externo'] = df_comparativa['stock_kardex'].isna()

    # Rellena con 0 los stocks de productos que solo existen en uno de los inventarios.
    df_comparativa['stock_farhos'] = df_comparativa['stock_farhos'].fillna(0)
    df_comparativa['stock_kardex'] = df_comparativa['stock_kardex'].fillna(0)

    # Consolida la columna de descripción. Usa la de Farhos si existe, si no, la de Kardex.
    df_comparativa['descripcion'] = df_comparativa['descripcion_farhos'].fillna(df_comparativa['descripcion_kardex'])
    
    # --- Cálculo de Diferencia ---
    # Calcula la diferencia de stock (Kardex - Farhos).
    df_comparativa['diferencia'] = df_comparativa['stock_farhos'] - df_comparativa['stock_kardex']

    # --- Formato Final ---
    # Selecciona y ordena las columnas para el informe final.
    df_final = df_comparativa[[
        'codigo', 
        'descripcion', 
        'externo',
        'stock_farhos', 
        'stock_kardex', 
        'diferencia'
    ]]

    # Renombra las columnas para que sean más claras en la tabla de resultados.
    df_final.rename(columns={
        'stock_farhos': 'Stock Farhos',
        'stock_kardex': 'Stock Kardex',
        'diferencia': 'Diferencia'
    }, inplace=True)

    return df_final
