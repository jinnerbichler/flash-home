from fabric.api import run, env, task, put, cd, local, sudo

env.use_ssh_config = True
env.hosts = ['iota_node']


@task(default=True)
def deploy_iri():
    run('mkdir -p /srv/private-tangle/')
    with cd('/srv/private-tangle'):
        put('.', '.')
        run('docker-compose --project-name private-tangle pull')
        run('docker-compose --project-name private-tangle up -d --force-recreate iri')


@task
def deploy_tools():
    with cd('/srv/private-tangle'):
        put('.', '.')
        run('docker-compose --project-name private-tangle pull')
        run('docker-compose --project-name private-tangle up -d --no-deps --force-recreate coordinator explorer')


@task
def stop():
    with cd('/srv/private-tangle'):
        run('docker-compose --project-name private-tangle stop')


@task
def logs():
    with cd('/srv/private-tangle'):
        run('docker-compose --project-name private-tangle logs -f --tail 100')


@task
def logs_all():
    with cd('/srv/private-tangle'):
        run('docker-compose logs -f')
