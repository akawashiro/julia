# メモ

Ruby の JIT での高速化は 2~3倍程度である。
[https://speed.yjit.org/](https://speed.yjit.org/)

一方 Julia は JIT で64倍程度高速化されている。
これはインタプリタの実装が悪そう。
```
$ ../julia --version
julia version 1.11.2
$ time ../julia nbody.jl 1> /dev/null
../julia nbody.jl > /dev/null  1.28s user 0.19s system 91% cpu 1.598 total
$ time ../julia --compile=no --compiled-modules=no nbody.jl 1> /dev/null
...
../julia --compile=no --compiled-modules=no nbody.jl > /dev/null  82.30s user 0.23s system 100% cpu 1:22.43 total
```

```
$ sudo ./nbody_profile.sh
$ sudo perf report --input nbody_compile_no.profile --no-children -Mintel
```

`jl_is_gotonode(stmt)` とかが遅い
