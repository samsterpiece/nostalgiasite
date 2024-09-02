import os
from celery import Celery
from kombu import Exchange, Queue
from celery.signals import worker_ready

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nostalgiasite.settings')

app = Celery('nostalgiasite')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Define default queue
app.conf.task_default_queue = 'default'
app.conf.task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
)

@worker_ready.connect
def at_start(sender, **kwargs):
    with sender.app.connection() as conn:
        sender.app.send_task('nostalgia_app.tasks.check_rabbitmq_connection', connection=conn)

@app.task(name='nostalgia_app.tasks.check_rabbitmq_connection')
def check_rabbitmq_connection():
    try:
        app.connection().ensure_connection(max_retries=3)
        print("Successfully connected to RabbitMQ")
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {str(e)}")

if __name__ == '__main__':
    app.start()