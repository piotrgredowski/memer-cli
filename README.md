# `memer`

A CLI for all your memes.

**Installation**: 

_Note_: We reccomend to install it via UV. However, you can install it any way you want.
1. [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
2. Install memer as a tool:
```sh
uv tool install --from git+https://github.com/zaremb/memer memer
```
3. (Optional) Pull default meme templates:
```sh
memer templates pull --defaults
```
4. Create memes, for example:
```sh
memer create --template-name "This Little Maneuver" --bottom-text "THIS LITTLE MANEUVER IS GONNA COST US 1337 COMMITS"
```

**Usage**:

```console
$ memer [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-v, --verbose`: Enable debug mode
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `create`: Create a meme using the specified template...
* `config`: Configuration related commands.
* `templates`: Meme template related commands.

## `memer create`

Create a meme using the specified template and text options.

**Usage**:

```console
$ memer create [OPTIONS]
```

**Options**:

* `-n, --template-name TEXT`: The name of the meme template to use. If provided name is a path, it will be used as a template.  [required]
* `-t, --top-text TEXT`: The text to display at the top of the meme.
* `-b, --bottom-text TEXT`: The text to display at the bottom of the meme.
* `-o, --output-path PATH`: The path where the generated meme will be saved.
* `--help`: Show this message and exit.

## `memer config`

Configuration related commands.

**Usage**:

```console
$ memer config [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `show`: Logs the configuration.
* `path`: Shows the path to the configuration.
* `edit`: Opens the configuration in the default...

### `memer config show`

Logs the configuration.

**Usage**:

```console
$ memer config show [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `memer config path`

Shows the path to the configuration.

**Usage**:

```console
$ memer config path [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `memer config edit`

Opens the configuration in the default editor.

**Usage**:

```console
$ memer config edit [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `memer templates`

Meme template related commands.

**Usage**:

```console
$ memer templates [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `list`: Lists the available templates.
* `search`: Searches for templates that match the...
* `pull`: Pulls meme templates from various sources...

### `memer templates list`

Lists the available templates.

Args:
    verbose (bool): If True, enables verbose output which includes the
        template's name, path, and key.
        If False, only the template's name is displayed.

Returns:
    None

**Usage**:

```console
$ memer templates list [OPTIONS]
```

**Options**:

* `-v, --verbose`: Enable verbose output
* `--help`: Show this message and exit.

### `memer templates search`

Searches for templates that match the given phrase and prints the results.

Args:
    phrase (str): The phrase to search for in the template names.

Returns:
    None

**Usage**:

```console
$ memer templates search [OPTIONS] PHRASE
```

**Arguments**:

* `PHRASE`: [required]

**Options**:

* `--help`: Show this message and exit.

### `memer templates pull`

Pulls meme templates from various sources and saves them to the user data template path.

Parameters:
url (str | None): The URL of the meme template to pull. Specified with --url or -u option.
name (str | None): The name to assign to the pulled meme template.
Specified with --name or -n option.
from_file (Path | None): The path to a file containing URLs of meme templates to pull
Specified with --from-file or -f option.
defaults (bool): Flag to pull default meme templates. Specified with --defaults or -d option.

**Usage**:

```console
$ memer templates pull [OPTIONS]
```

**Options**:

* `-u, --url TEXT`
* `-n, --name TEXT`
* `-f, --from-file PATH`
* `-d, --defaults`
* `--help`: Show this message and exit.
