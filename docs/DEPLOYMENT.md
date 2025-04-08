# Deployment

## Using pytest-ranking in fixed location

If your CI runs different test builds in a fixed location, e.g., a project folder in specific machine, you can directly use `pytest-ranking` after installation without additional setup.

## Using pytest-ranking in Github Actions

If your CI workflow always starts a new virtual machine to run a test build, you need to set up the CI to be able to pass `pytest` cache data across test builds.
Here, we use GitHub Actions as an example.

### Add pytest-ranking to project dependency


You can add `pytest-ranking` as a dependency by adding a installation job before the job that runs `pytest ...` (a job is often specified by `-name: `) in the workflow file:

```yml
    - name: Install pytest-ranking related
      run: pip install pytest-ranking
```

Alternatively, depending on where the forked project puts its dependency, e.g., can be in `setup.py`, `pyproejct.toml`, you can also add the `pytest-ranking` to the build/test dependency, but best not to specify version.


#### If the project uses `Tox`

Add `pytest-ranking` to the `deps` of `[testenv]` in `./tox.ini`:
```ini
[testenv]
deps =
  ; ...
  pytest-ranking
  pytest-json-report
```


### Setup pytest_cache

Before the job in the workflow file that runs the `pytest ...` but after the `pytest-ranking` installation job, add the job that restores cache from the latest run if such run exists:

```yml
    - name: Restore pytest-ranking cache
      id: restore-pytest-ranking-cache
      if: always()
      uses: actions/cache/restore@v4
      with:
        path: ${{ github.workspace }}/.pytest_cache/v/pytest_ranking_data
        key: pytest-ranking-cache-${{ github.workflow }}-${{ runner.os }}-${{ matrix.python }}
    # --------below is the job for running pytest
    -name: pytest
        ...
```

And after the job that runs `pytest ...` command, add the job that caches result of this run:

```yml
    -name: pytest
        ...
    # --------above is the job for running pytest
    - name: Save pytest-ranking cache
      id: save-pytest-ranking-cache
      if: always()
      uses: actions/cache/save@v4
      with:
        path: ${{ github.workspace }}/.pytest_cache/v/pytest_ranking_data
        key: pytest-ranking-cache-${{ github.workflow }}-${{ runner.os }}-${{ matrix.python }}-${{ github.run_id }}
```

#### If the project uses `Tox`

You need to manually identify the location of `./pytest_cache` folder when tox is used by inspecting the workflow run log, it looks like this:
```
============================= test session starts ==============================
...
cachedir: .tox/TOX_ENV_NAME/.pytest_cache
...
```

The `cachedir` is what we are looking for. In this example, we need to replace `path: ${{ github.workspace }}/.pytest_cache/v/pytest_ranking_data` into `path: ${{ github.workspace }}/.tox/TOX_ENV_NAME/v/pytest_ranking_data` in both the `restore` and `save` cache jobs above in the workflow file.

#### Alternative to `actions/cache`

[`actions/cache`](https://github.com/actions/cache) is one way to allow data from a previous GutHub Actions CI build to be used in the future build.
One limitation of `actions/cache` is that its cache has a retention period and the total size of all caches for a repository is limited ([reference](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/caching-dependencies-to-speed-up-workflows#usage-limits-and-eviction-policy)).


One can also setup a more stable cache storage, e.g., a remote server, and use other GitHub actions to transfer cache data from/to a specific destination. Example actions are [`scp-action`](https://github.com/appleboy/scp-action) and [`copy-via-ssh`](https://github.com/marketplace/actions/copy-via-ssh)
