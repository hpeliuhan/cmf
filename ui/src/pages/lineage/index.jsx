/***
* Copyright (2023) Hewlett Packard Enterprise Development LP
*
* Licensed under the Apache License, Version 2.0 (the "License");
* You may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
***/


import React, { useEffect, useState } from "react";
import FastAPIClient from "../../client";
import config from "../../config";
import DashboardHeader from "../../components/DashboardHeader";
import Footer from "../../components/Footer";
import LineageSidebar from "../../components/LineageSidebar";
import LineageTypeSidebar from "./LineageTypeSidebar";
import LineageArtifacts from "../../components/LineageArtifacts";
import TangledTree from "../../components/TangledTree";
import ExecutionDropdown from "../../components/ExecutionDropdown";
import ExecutionTree from "../../components/ExecutionTree";
import ExecutionTangledDropdown from "../../components/ExecutionTangledDropdown";
import Loader from "../../components/Loader";

const client = new FastAPIClient(config);

const Lineage = () => {
  const [pipelines, setPipelines] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const LineageTypes = ['Artifact_Tree', 'Execution_Tree'];
  const [selectedLineageType, setSelectedLineageType] = useState('Artifact_Tree');
  const [selectedExecutionType, setSelectedExecutionType] = useState(null);
  const [lineageData, setLineageData] = useState(null);
  const [executionData, setExecutionData] = useState(null);
  const [lineageArtifactsKey, setLineageArtifactsKey] = useState(0);
  const [execDropdownData,setExecDropdownData] = useState([]);
  const [artitreeData, setArtiTreeData] = useState(null);
  const [loading, setLoading] = useState(true);

  // fetching list of pipelines
  useEffect(() => {
    fetchPipelines();
  }, []);

  const fetchPipelines = () => {
    setLoading(true);
    client.getPipelines("").then((data) => {
      setPipelines(data);
      setSelectedPipeline(data[0]);
      // when pipeline is updated we need to update the lineage selection too
      // in my opinion this is also not needed as we have selectedLineage has
      // default value
      if (data[0]) {
        setSelectedLineageType(LineageTypes[0]);
        // call artifact lineage as it is default
        fetchArtifactTree(data[0]);
      }
      setLoading(false);
    });
  };
  const handlePipelineClick = (pipeline) => {
    setLineageData(null);
    setExecutionData(null); 
    setArtiTreeData(null);
    setSelectedPipeline(pipeline);
    // when pipeline is updated we need to update the lineage selection too
    // this is also not needed as selectedLineage has default value
    // setSelectedLineageType(LineageTypes[0]);
     if (selectedPipeline) {
       if (selectedLineageType === "Artifacts") {
          //call artifact lineage as it is default
          fetchArtifactLineage(pipeline);
       }
       else if (selectedLineageType === "Execution" || selectedLineageType === "Execution_Tree") {
          fetchExecutionTypes(pipeline, selectedLineageType);
       }
       else {
          
          fetchArtifactTree(pipeline);
      }}
  };

  const handleLineageTypeClick = (lineageType) => {
    setLineageData(null);
    setExecutionData(null);
    setArtiTreeData(null);
    setSelectedLineageType(lineageType);
    if (lineageType === "Artifacts") {
      fetchArtifactLineage(selectedPipeline);
    }
    else if (lineageType === "Execution" || lineageType === "Execution_Tree" ) {
      fetchExecutionTypes(selectedPipeline, lineageType);
    }
    else {
      fetchArtifactTree(selectedPipeline);
    }
  };  


  const fetchArtifactLineage = (pipelineName) => {
    setLoading(true);
    client.getArtifactLineage(pipelineName).then((data) => {    
        if (data === null) { 
        setLineageData(null);
        }
        setLineageData(data);
        setLoading(false);
    });
    setLineageArtifactsKey((prevKey) => prevKey + 1);
  };

  const fetchArtifactTree = (pipelineName) => {
    setLoading(true);
    client.getArtiTreeLineage(pipelineName).then((data) => {    
      if (data === null) { 
          setArtiTreeData(null);
      }
      setArtiTreeData(data);
      setLoading(false);
    });
  };

  const fetchExecutionTypes = (pipelineName, lineageType) => {
    setLoading(true);
    client.getExecutionTypes(pipelineName).then((data) => {    
        if (data === null ) {
           setExecDropdownData(null);
        }
        else {
        setExecDropdownData(data);
        setSelectedExecutionType(data[0]);     // data[0] = "Prepare_3f45"
        // method used such that even with multiple "_" it will get right execution_name and uuid
        const uuid= (data[0].split("_").pop());     // 3f45
        if (lineageType === "Execution") {
            fetchExecutionLineage(pipelineName, uuid);
            }
        else {
            fetchExecTree(pipelineName,uuid);
            }
        }
        setLoading(false);
    });
    setLineageArtifactsKey((prevKey) => prevKey + 1);
  };

  // used for execution drop down
  const handleExecutionClick = (executionType) => {
    setExecutionData(null);
    
    setSelectedExecutionType(executionType);
    const uuid= (executionType.split("_").pop());
    fetchExecutionLineage(selectedPipeline, uuid);
  };  

  // used for execution drop down
  const handleTreeClick = (executionType) => {
    setExecutionData(null);
    setSelectedExecutionType(executionType);
    const uuid= (executionType.split("_").pop());
    fetchExecTree(selectedPipeline, uuid);
  };  

  const fetchExecutionLineage = (pipelineName,uuid) => {
    setLoading(true);
    client.getExecutionLineage(pipelineName,uuid).then((data) => {    
      if (data === null) {
          setExecutionData(null);
      }
      setExecutionData(data);
      setLoading(false);
    });
  };

  const fetchExecTree = (pipelineName,exec_type) => {
    setLoading(true);
    client.getExecTreeLineage(pipelineName,exec_type).then((data) => {    
      setExecutionData(data);
      setLoading(false);
    });
  };

  return (
    <>
      <section
        className="flex flex-col bg-white"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />

        <div className="container">
          <div className="flex flex-row">
            <LineageSidebar
              pipelines={pipelines}
              handlePipelineClick={handlePipelineClick}
            />
          <div className="container justify-center items-center mx-auto px-4">
            <div className="flex flex-col">
             {selectedPipeline !== null && (
                <LineageTypeSidebar
                  LineageTypes={LineageTypes}
                  handleLineageTypeClick= {handleLineageTypeClick}
                />
             )}
            </div>
            <div className="container">
              { loading && <Loader /> }
              {!loading && selectedPipeline !== null && selectedLineageType === "Artifacts" && lineageData !== null && (
                <LineageArtifacts key={lineageArtifactsKey}  data={lineageData} />
              )}
              {!loading && selectedPipeline !== null && selectedLineageType === "Execution" && execDropdownData !== null  && executionData !== null &&(
                <div>
                  <ExecutionDropdown data={execDropdownData} exec_type={selectedExecutionType} handleExecutionClick= {handleExecutionClick} />
                </div>
              )}
              {!loading && selectedPipeline !== null && selectedLineageType === "Execution" && execDropdownData !== null  && executionData !== null &&(
                <div>
                  <LineageArtifacts key={lineageArtifactsKey} data={executionData} />
                </div>
              )}
              {!loading && selectedPipeline !== null && selectedLineageType === "Execution_Tree" && execDropdownData !== null   &&(
                <div>
                  <ExecutionTangledDropdown data={execDropdownData} exec_type={selectedExecutionType} handleTreeClick= {handleTreeClick} />
                </div>
              )}
              {!loading && selectedPipeline !== null && selectedLineageType === "Execution_Tree" && execDropdownData !== null  && executionData !== null &&(
                <div style={{ justifyContent: 'center', alignItems: 'center' }}>
                  <ExecutionTree key={lineageArtifactsKey} data={executionData} />
                </div>
              )}
              {!loading && selectedPipeline !== null && selectedLineageType === "Artifact_Tree" && artitreeData !== null &&(
                <div style={{ justifyContent: 'center', alignItems: 'center' }}>
                  <TangledTree key={lineageArtifactsKey} data={artitreeData} />
                </div>
              )}
            </div>
          </div>
        </div>
       </div>
        <Footer />
      </section>
    </>
  );
};

export default Lineage;