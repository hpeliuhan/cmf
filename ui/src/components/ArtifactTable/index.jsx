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


// ArtifactTable.jsx
import React, { useState, useEffect } from "react";
import "./index.css";
import Popup from "../../components/Popup";
import FastAPIClient from "../../client";
import config from "../../config";

const client = new FastAPIClient(config);

const ArtifactTable = ({ artifacts, ArtifactType, onSort }) => {

  // Default sorting order
  const [sortOrder, setSortOrder] = useState(onSort);
  const [sortedData, setSortedData] = useState([]);  

  const [expandedRow, setExpandedRow] = useState(null);
  const [showPopup, setShowPopup] = useState(false);
  const [popupData, setPopupData] = useState('');

  const consistentColumns = [];


  useEffect(() => {
    // Set initial sorting order when component mounts
    setSortedData([...artifacts]);
  }, [artifacts]);

  const handleSort = () => {
    // Initially all data is in mixed format 
    // After the data is in asc order
    // then it is in desc order
    const newSortOrder = sortOrder === "desc" ? "asc" : sortOrder === "asc" ? "desc" : "asc";
    setSortOrder(newSortOrder);
    const sorted = [...artifacts].sort((a, b) => {
        if(newSortOrder === "asc"){
            return a.name.localeCompare(b.name);
        }else{
            return b.name.localeCompare(a.name);        
        }
    });
    setSortedData(sorted); // Notify parent component about sorting change
  };


  const toggleRow = (rowId) => {
    if (expandedRow === rowId) {
      setExpandedRow(null);
    } else {
      setExpandedRow(rowId);
    }
  };

    const handleLinkClick = (model_id) => {
        client.getModelCard(model_id).then((data) => {    
          console.log(data);
          setPopupData(data);
          setShowPopup(true);
      });
    };

    const handleClosePopup = () => {
        setShowPopup(false);
    };
    
    const renderArrow = () => {
      if (sortOrder === "desc"){
        return <span className="text-2xl cursor-pointer">&#8595;</span> //data is in desc order ---> ↓
      } else if (sortOrder === "asc"){
        return <span className="text-2xl cursor-pointer">&#8593;</span> //data is in asc order ----> ↑
      } else{
        return <span className="text-2xl cursor-pointer">&#8597;</span> //data is in initial order -----------> ↕
      }
    }
  
  return (
    <div className="container flex flex-col">
      <div className="overflow-x-auto">
        <div className="p-1.5 w-full inline-block align-middle">
          <table className="min-w-full divide-y divide-gray-200 border-4">
            <thead className="bg-gray-100">
              <tr className="text-xs font-bold text-left text-gray-500 uppercase">
                <th scope="col" className="id px-6 py-3"></th>
                <th scope="col" className="id px-6 py-3">
                  id
                </th>
                <th
                  scope="col"
                  onClick={handleSort}
                  className="name px-6 py-3"
                >
                  name&nbsp; {renderArrow()}
                </th>
                {ArtifactType === "Model" && (
                <th scope="col" className="model_card px-6 py-3">
                  Model_Card
                </th>
                )}

		<th scope="col" className="exe_uuid px-6 py-3">
                  execution_type_name
                </th>
                <th scope="col" className="url px-6 py-3">
                  Url
                </th>
                <th scope="col" className="uri px-6 py-3">
                  Uri
                </th>
                <th scope="col" className="git_repo px-6 py-3">
                  Git_Repo
                </th>
                <th scope="col" className="commit px-6 py-3">
                  Commit
                </th>
              </tr>
            </thead>
            <tbody className="body divide-y divide-gray-200">
              {sortedData.length > 0 && sortedData.map((data, index) => (
                <React.Fragment key={index}>
                  <tr
                    key={index}
                    className="text-sm font-medium text-gray-800"
                  >
                    <td className="px-6 py-4 cursor-pointer" onClick={() => toggleRow(index)}>
                      {expandedRow === index ? "-" : "+"}
                    </td>
                    <td className="px-6 py-4">{data.id}</td>
                    <td className="px-6 py-4">{data.name}</td>
                    {ArtifactType === "Model" && (
                    <td className="px-6 py-4">
                        <a href="#" onClick={(e) => { e.preventDefault(); handleLinkClick(data.id); }}>Open Model Card</a>
                        <Popup show={showPopup} model_data={popupData} onClose={handleClosePopup} />
                    </td>
                    )}
                    <td className="px-6 py-4">{data.execution_type_name}</td>
                    <td className="px-6 py-4">{data.url}</td>
                    <td className="px-6 py-4">{data.uri}</td>
                    <td className="px-6 py-4">{data.git_repo}</td>
                    <td className="px-6 py-4">{data.Commit}</td>
                  </tr>
                  {expandedRow === index && (
                    <tr>
                      <td colSpan="4">
                        <table className="expanded-table">
                          <tbody>
                            {Object.entries(data).map(([key, value]) => {
                              if (
                                !consistentColumns.includes(key) &&
                                value != null
                              ) {
                                return (
                                  <React.Fragment key={key}>
                                    <tr>
                                      <td key={key}>{key}</td>
                                      <td key={value}>
                                        {value ? value : "Null"}
                                      </td>
                                    </tr>
                                  </React.Fragment>
                                );
                              }
                              return null;
                            })}
                          </tbody>
                        </table>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ArtifactTable;