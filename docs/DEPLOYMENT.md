# Deployment

## Using pytest-rtp in fixed location

If your CI runs different test builds in a fixed location, e.g., a project folder in specific machine, you can directly use `pytest-rtp` after installation without additional setup.

## Using pytest-rtp in Github Actions

If your CI workflow always starts a new virtual machine to run a test build, you need to set up the CI to be able to pass `pytest` cache data across test builds.
Here, we use GitHub Actions as an example.

### Add pytest-rtp to project dependency


You can add `pytest-rtp` as a dependency by adding a installation job before the job that runs `pytest ...` (a job is often specified by `-name: `) in the workflow file:

```yml
    - name: Install pytest-rtp related
      run: pip install pytest-rtp
```

Alternatively, depending on where the forked project puts its dependency, e.g., can be in `setup.py`, `pyproejct.toml`, you can also add the `pytest-rtp` to the build/test dependency, but best not to specify version.


#### If the project uses `Tox`

Add `pytest-rtp` to the `deps` of `[testenv]` in `./tox.ini`:
```ini
[testenv]
deps =
  ; ...
  pytest-rtp
  pytest-json-report
```


### Setup pytest_cache

Before the job in the workflow file that runs the `pytest ...` but after the `pytest-rtp` installation job, add the job that restores cache from the latest run if such run exists:

```yml
    - name: Restore pytest-rtp cache
      id: restore-pytest-rtp-cache
      if: always()
      uses: actions/cache/restore@v4
      with:
        path: ${{ github.workspace }}/.pytest_cache/v/pytest_rtp_data
        key: pytest-rtp-cache-${{ github.workflow }}-${{ runner.os }}-${{ matrix.python }}
    # --------below is the job for running pytest
    -name: pytest
        ...
```

And after the job that runs `pytest ...` command, add the job that caches result of this run:

```yml
    -name: pytest
        ...
    # --------above is the job for running pytest
    - name: Save pytest-rtp cache
      id: save-pytest-rtp-cache
      if: always()
      uses: actions/cache/save@v4
      with:
        path: ${{ github.workspace }}/.pytest_cache/v/pytest_rtp_data
        key: pytest-rtp-cache-${{ github.workflow }}-${{ runner.os }}-${{ matrix.python }}-${{ github.run_id }}
```

#### If the project uses `Tox`

You need to manually identify the location of `./pytest_cache` folder when tox is used by inspecting the workflow run log, it looks like this:
```
============================= test session starts ==============================
...
cachedir: .tox/TOX_ENV_NAME/.pytest_cache
...
```

The `cachedir` is what we are looking for. In this example, we need to replace `path: ${{ github.workspace }}/.pytest_cache/v/pytest_rtp_data` into `path: ${{ github.workspace }}/.tox/TOX_ENV_NAME/v/pytest_rtp_data` in both the `restore` and `save` cache jobs above in the workflow file.
