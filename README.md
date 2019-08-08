# bxcommon
Common python components for bloXroute Python projects.

## Static Type Analysis

Basic usage:
```bash
$ ./check.sh
```
This will install a `virtualenv` at `.venv`, and execute the tests. You **must** do this at least once, even if you use
`virtualenvwrapper` , since `.pyre_configuration` points to `.venv` to reference Python package dependencies. **Do not
run this script while your `virtualenvwrapper` environment is active**, as it will create endless symlinks and you will
have to delete `.venv`. So if you use `virtualenvwrapper` your flow should look like this:
```bash
$ deactivate
$ ./check.sh
$ workon bloxroute # or whatever your virtualenv name is
$ pyre check
```

Incremental mode (faster for local development, recommended):
```bash
$ brew install watchman
$ ./check-server.sh
$ source .venv/bin/activate
$ pyre # call this anytime you make changes to get fast analysis
```
`check-server.sh` is interchangeable with `check.sh`. Either can be run repeatedly successfully. If you use 
`virtualenvwrapper`, do something like this:
```bash
$ deactivate
$ brew install watchman
$ ./check-server.sh
$ workon bloxroute
$ pyre # on subsequent changes
```
