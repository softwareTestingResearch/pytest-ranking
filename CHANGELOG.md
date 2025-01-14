
# Changelog

0.3.3 (2024-12-24)
----

* order dependency

0.3.2 (2024-12-23)
----

* refine test group level definition and extraction
* use pytest test discovery order as default

0.3.1 (2024-06-06)
----

* support ranking tests at different granularity levels (PUT, method, file, folder)
* add plugin summary via pytest_terminal_summary

0.3.0 (2024-05-12)
----

* Fix attribute initialization in change tracker for Python 3.11 and lower versions


0.2.8 (2024-05-08)
----

* Make pytest-xdist compatible for random and change-related heuristics


0.2.7 (2024-03-18)
----

* Add option to run tests in random order
* Improve documentation




0.2.0 (2024-02-16)
----

* Add textual similarity between tests and changed files since last run as the third heuristic
* Weight normalization
* History length as an optional argument
* Rename plugin to `pytest-ranking`


0.1.0 (2023-12-04)
----

* First release on PyPI
