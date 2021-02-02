import pandas as pd
from planetagrandt import obtain_links
from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago

args = {
    'owner': 'Pablo',
    'start_date': days_ago(10)),
}

dag = DAG(
    dag_id='testing_python_operator',
    default_args=args,
    schedule_interval='0 0 * * 3',
    tags=['testing']
)

def planetagrandt_links():
    url = 'https://www.planetagrandt.com.ar/search/label/Estad%C3%ADsticas'
    validate = pd.read_csv('grandtlinks.csv')
    validate.dates = validate.dates.apply(pd.to_datetime)

    links = []
    dates = []
    
    df = obtain_links(url, links, dates, validate)

    df.to_csv('grandtlinks.csv', index=False, mode='a', header=False)

try_this = PythonOperator(
    task_id='obtaining links from planetagrandt',
    provide_context=True,
    python_callable=planetagrandt_links,
    dag=dag,
)