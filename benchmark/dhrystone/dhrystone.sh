echo test > /sys/power/wake_lock
input keyevent 26
cat /sys/devices/system/cpu/cpu*/online
sleep 5
#record CPU frequencies right before running Dhrystone
echo "Pre-benchmark"  > /data/local/tmp/dhrystone.log
echo "Time in state"  >> /data/local/tmp/dhrystone.log
cat /sys/devices/system/cpu/cpu*/cpufreq/stats/time_in_state   >> /data/local/tmp/dhrystone.log
echo "Current CPU frequencies"   >> /data/local/tmp/dhrystone.log
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq   >> /data/local/tmp/dhrystone.log

#run Dhrystone until thermal throttling is detected 
#           or until the timeout of 90 seconds is reached
cur_time=$(date +%s)
end_time=$(($cur_time+90))

cur_freq_apc7=$(cat /sys/devices/system/cpu/cpu7/cpufreq/scaling_cur_freq)

/data/local/tmp/./busybox date +%s
while [ $cur_time -lt $end_time ]; do
	/data/local/tmp/dhrystone64_bit.elf < /data/local/tmp/input.txt & /data/local/tmp/dhrystone64_bit.elf < /data/local/tmp/input.txt 
	cur_time=$(date +%s)
	if [ $cur_freq_apc4 -ne $fmax ]
	then
		end_time=$cur_time
	fi

	cur_freq_apc7=$(cat /sys/devices/system/cpu/cpu7/cpufreq/scaling_cur_freq)
	
done

input keyevent 26
sleep 2


#release wake lock
echo test > /sys/power/wake_unlock
sleep 2

