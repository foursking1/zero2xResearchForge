Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and ($_.CommandLine -match 'test_pretrain|run_all|run_baselines') } | ForEach-Object {
    $cpu = ($_.KernelModeTime + $_.UserModeTime) / 10000000
    $cmd = ($_.CommandLine -split '\\')[-1]
    "{0} cpu={1:N0}s cmd={2}" -f $_.ProcessId, $cpu, $cmd
}
