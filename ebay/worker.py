import django_rq

if __name__ == "__main__":
    worker = django_rq.get_worker('default')
