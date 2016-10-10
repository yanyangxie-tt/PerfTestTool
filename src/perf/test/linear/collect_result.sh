#!/bin/sh

script_dir=${script_dir:-`(cd "$(dirname "$0")"; pwd)`}
collect_result_scipt_file="${script_dir}/collect_test_result.py"

if [ ! -f "$collect_result_scipt_file" ]; then
    echo "Not found the collect test result script ${collect_result_scipt_file}"
    exit 1
fi

echo "python ${collect_result_scipt_file}"
python ${collect_result_scipt_file}

if [[ $? != 0 ]];then
	echo "Do test result collection failed. ${ret}"
	exit 2
fi