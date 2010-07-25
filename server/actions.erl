-module(actions).
-export([
    login/0,
    logout/0
]).
-vsn(0.1).

-include("definitions.hrl").


login() ->
    error_logger:info_msg("logging in~n"),
    messenger ! {register, self()}.


logout() ->
    error_logger:info_msg("logging out~n"),
    messenger ! {unregister, self()}.
