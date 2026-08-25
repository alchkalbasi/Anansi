# system-setup TODO List

* [x] create role stracture
* [x] create main.yml task
    - inside tasks:
        * [x] system dir
            - [x] userconf.yml
                - [x] ensure user exists
                - [x] passwordless sudo
                - [x] workspace dir
                - [x] check ownership of ~
            - [x] ssh.yml
                - [x] install ssh
                - [x] ensure .ssh exists
                - [x] add or create keys
                - [x] add authorized_keys
                - [x] create ssh config file from files
            - [x] apt.yml
                - [x] add sources lists
                - [x] apt update
                - [x] apt full upgrade
            - [x] config.yml
                - [x] set zsh default
                - [x] update zshrc
                - [x] zsh aliases
                - [x] config vimrc
                - [x] config default editor
                - [x] config terminator 
        * [x] devtools dir
            - [x] tools.yml
        * [x] apps dir
            - [x] snapd
            - [x] telegram
            - [x] nekoray
            - [x] zsh
            - [x] oh-my-zsh
            - [x] zsh-autosuggestions
            - [x] zsh-syntax-highlighting
            - [x] vim-plugins
            - [x] vscode
            - [x] chrome