import pandas as pd
import re

url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTiIT-pt294csANmtweayBA5KwRptwJ1M_WPx7XyO2kXamK6oZFsRfQZJUm-P7Uj7X2mQvr6nR7EcEW/pubhtml#'

dfs = pd.read_html(url, encoding='UTF-8')

### Lets get General data
df = dfs[1]


informacion_partido = df.loc[0, 'Unnamed: 0']

torneo = int(re.search('(\d+)\/', informacion_partido).group(1))
fecha = int(re.search('FECHA (\d+)$', match_information).group(1))

df.drop('Unnamed: 0', axis=1, inplace=True)

df = df.iloc[7:, :]
df = df.rename(columns=df.iloc[0]).drop(df.index[0])
df = df.reset_index(drop=True)

df.to_csv(f'planetagrandt_torneo{torneo}_fecha{fecha}.csv')