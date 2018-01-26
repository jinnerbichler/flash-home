from fabric.api import run, env, task, put, cd, local, sudo

env.use_ssh_config = True
env.hosts = ['flash_home']


@task(default=True)
def deploy():
    with cd('/srv/flash-home'):
        run('git pull origin master')

        run('echo "COFFEE_FLASH_BASE_URL=http://flash-home.duckdns.org:3000/" > env')
        run('echo "PROVIDER_FLASH_BASE_URL=http://flash-home.duckdns.org:3001/" >> env')

        run('docker-compose --project-name flash-home pull')
        run('docker-compose --project-name flash-home up -d --build --force-recreate')


@task
def init():
    run('mkdir -p /srv/flash-home/')
    with cd('/srv/flash-home'):
        run('git clone --recursive https://github.com/jinnerbichler/flash-home')


@task
def logs():
    with cd('/srv/flash-home'):
        run('docker-compose --project-name flash-home logs -f --tail 100')
