# SmartContractsBenchmarking

### Benchmarking System for Ethereum Smart Contracts

"The benchmarking system is to allow measuring the execution time of Ethereum smart contracts. It covers contract creation and contract invocation. It is worth noting both contract creation and invocation are made by submitting a transaction to the Ethereum network. We developed the benchmarking system to be run on top of Pyethereum client; and we might extend it in the future to support other clients like Go." For more details we refer the reader to our paper "Performance benchmarking of smart contracts to assess miner incentives in Ethereum".

#### Requirements:

* Install PyEthereum client in your local machine

* Install All python package required by the benchmarking system such as pandas etc

#### To run the code, type the following command: 

> python contractBenchSystem.py state.json

#### Comments:
* The data set and final results files are big and cannot be uploaded to Github. Instead, we upload a sample data set of 50K transactions (DataSet8.xlsx) and its results (DataSet8Results.xlsx). So, you can try the benchmark system and obtain the results.

* To get the full data set with its results, please contact me at alharbi.maher@gmail.com
