import django_rq

worker = django_rq.get_worker()
worker.work()