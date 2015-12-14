
outrunner_watch_on_cwd() {
    # Don't do anything if not connected to a terminal.
    [[ -t 1 ]] || return
    shell_pid=$$
    git_root=$(git rev-parse --show-toplevel 2> /dev/null)
    if (( $? != 0 )); then
        git_root=""
    fi
# if there is an active path and it's not the same as current git root (could be empty), unwatch current
    if [[ $git_root != $OUTRUNNER_ACTIVE_PATH ]]; then
        if [[ -n $OUTRUNNER_ACTIVE_PATH ]]; then
            outrunner unwatch $OUTRUNNER_ACTIVE_PATH
        fi

        if [[ "$git_root" != "" ]]; then
            outrunner watch $git_root
            if (( $? == 0 )); then
                export OUTRUNNER_ACTIVE_PATH=$(pwd)
            fi
        elif [[ -n $OUTRUNNER_ACTIVE_PATH ]]; then
            unset OUTRUNNER_ACTIVE_PATH
        fi
    fi
}

outrunner_exit(){
    if [[ -n $OUTRUNNER_ACTIVE_PATH ]]; then
    outrunner unwatch $OUTRUNNER_ACTIVE_PATH
    fi
}

autoload -U add-zsh-hook
add-zsh-hook chpwd outrunner_watch_on_cwd
add-zsh-hook zshexit outrunner_exit
