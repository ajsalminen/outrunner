outrunner
==========
  
Description
------------
outrunner is a task runner that keeps track of watched directories and runs
tasks when a file in one of the watched directories changes. It's still in the
early phases of development but should be functional if you don't kick it's
tires too much.
  
  
The current supported use case is automatically running [GNU
Global](gnu.org/software/global/) for a directory to update source code tag
files incrementally and automatically generate the full tag files when a watch
is set up for a project that does not yet have them. A zsh plugin is provided
for triggering this whenever the user enters a directory under git version control.
  
  
In the future this tool will hopefully start supporting othes taggers such as
ctags (universal-ctags, exuberant-ctags...), provide support for other shells and
editors (bash, emacs, vim...) and maybe other inotify/kqueue/FSEvents-based
watcher tools and completely different use cases.

Requirements
------------

outrunner depends on [Facebook's Watchman](https://github.com/facebook/watchman)
for setting up the watches and GNU global is the one source code tagger it
works with at the moment. Only shell currently supported is
[ZSH](http://www.zsh.org/).
  
The program is written in python and utilizes PyYAML.

Configuration
--------------

See outrunner.conf.yml for how to configure outrunner. The default configuration
can be replaced by placing the .outrunner.conf.yml dotfile in your home directory.

License
-------

MIT

See also
--------

* [maurizi's retag.rs](https://github.com/maurizi/retag.rs/) is a similar tool
  written in Rust.
* [Effortless Ctags with Git](http://tbaggery.com/2011/08/08/effortless-ctags-with-git.html) is a different approach that relies on git hooks instead of inotify-like functionality.
* [helm-gtags.el](https://github.com/syohex/emacs-helm-gtags) for Emacs and other similar packages provide automatic tagger updates when a file is saved from the editor
* [grunt](http://gruntjs.com/) and other similar task runners may have plugins that achieve similar things for a project.
