# Whole-function native reuse probe

`prototype.py` extracts the original DOS `ClrModePop` function from
`src/root/m0894.c`, changes only the function signature, four global bindings,
the loop index type, and the historical `far` qualifier, then compiles/runs it
against `SimTickState` with native GCC. It records the source-file SHA-256 and
line range in the generated file.

This intentionally small probe tests source reuse where the function is pure
state transformation and has no helper or platform calls. It is diagnostic
research code under `portable/research/`; generated output is not accepted
portable source, and the smoke test is not a DOS differential claim.

Run:

```powershell
python portable/research/source-reuse/prototype.py
```

The experiment does not establish that the ant-loop modules can be translated
by mechanical extraction. Their blockers are recorded in the supervisor
message and final task response.
