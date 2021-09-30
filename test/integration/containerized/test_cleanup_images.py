import shutil
import json
from base64 import b64decode
import os

import pytest

from ansible_runner.cleanup import cleanup_images, prune_images
from ansible_runner.defaults import default_container_image


@pytest.mark.parametrize('runtime', ['podman', 'docker'])
def test_cleanup_new_image(cli, runtime, tmp_path):
    if shutil.which(runtime) is None:
        pytest.skip(f'{runtime} is unavaialble')

    # Create new image just for this test with a unique layer
    special_string = "Verify this in test - 1QT4r18a7E"
dockerfile_path = tmp_path / 'Dockerfile'
dockerfile_path.write_text('\n'.join([
    'FROM {}'.format(default_container_image),
    'RUN echo {} > /tmp/for_test.txt'.format(special_string)
]))
image_name = 'quay.io/fortest/hasfile:latest'
build_cmd = [runtime, 'build', '--rm=true', '-t', image_name, '-f', str(dockerfile_path), str(tmp_path)]
    cli(build_cmd, bare=True)

    # get an id for the unique layer
    r = cli([runtime, 'images', image_name, '--format="{{.ID}}"'], bare=True)
    layer_id = r.stdout.strip()
    assert layer_id in cli([runtime, 'images'], bare=True).stdout

    # workaround for https://github.com/ansible/ansible-runner/issues/758
    tmp_path.joinpath('project').mkdir()

    # force no colors so that we can JSON load ad hoc output
    env_path = tmp_path.joinpath('env')
    env_path.mkdir()
    env_path.joinpath('envvars').write_text('{"ANSIBLE_NOCOLOR": "true"}')

    # assure that the image is usable in ansible-runner as an EE
    r = cli([
        'run', str(tmp_path), '-m', 'slurp', '-a', 'src=/tmp/for_test.txt', '--hosts=localhost', '--ident', 'for_test',
        '--container-image', image_name, '--process-isolation', '--process-isolation-executable', runtime
    ])
    stdout = r.stdout
    data = json.loads(stdout[stdout.index('{'):stdout.index('}') + 1])
    assert 'content' in data
    assert special_string == str(b64decode(data['content']).strip(), encoding='utf-8')

    image_ct = cleanup_images(images=[image_name], runtime=runtime)
    assert image_ct == 1
    prune_images(runtime=runtime)  # May or may not do anything, depends on docker / podman

    assert layer_id not in cli([runtime, 'images'], bare=True).stdout  # establishes that cleanup was genuine

    assert cleanup_images(images=[image_name], runtime=runtime) == 0  # should be no-op
