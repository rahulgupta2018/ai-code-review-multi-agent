// JavaScript utility functions with various code quality issues
// This file demonstrates common JavaScript anti-patterns and issues

const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Global variables (anti-pattern)
var globalCounter = 0;
let sharedData = {};

// Function with high complexity and multiple responsibilities
function processUserData(users, options) {
    let results = [];
    let errors = [];
    
    // Deeply nested conditionals and loops
    for (let i = 0; i < users.length; i++) {
        if (users[i] !== null && users[i] !== undefined) {
            if (typeof users[i] === 'object') {
                if (users[i].hasOwnProperty('id') && users[i].hasOwnProperty('name')) {
                    if (users[i].id > 0) {
                        if (users[i].name && users[i].name.length > 0) {
                            let processedUser = {
                                id: users[i].id,
                                name: users[i].name.trim(),
                                processed: true,
                                timestamp: new Date().toISOString()
                            };
                            
                            // More nested conditions
                            if (options && options.includeEmail) {
                                if (users[i].email) {
                                    if (validateEmail(users[i].email)) {
                                        processedUser.email = users[i].email.toLowerCase();
                                    } else {
                                        errors.push(`Invalid email for user ${users[i].id}: ${users[i].email}`);
                                    }
                                } else {
                                    errors.push(`Missing email for user ${users[i].id}`);
                                }
                            }
                            
                            if (options && options.includeAge) {
                                if (users[i].age !== undefined && users[i].age !== null) {
                                    if (typeof users[i].age === 'number' && users[i].age >= 0 && users[i].age <= 150) {
                                        processedUser.age = users[i].age;
                                        if (users[i].age >= 18) {
                                            processedUser.isAdult = true;
                                        } else {
                                            processedUser.isAdult = false;
                                        }
                                    } else {
                                        errors.push(`Invalid age for user ${users[i].id}: ${users[i].age}`);
                                    }
                                }
                            }
                            
                            results.push(processedUser);
                        } else {
                            errors.push(`Invalid name for user ${users[i].id}`);
                        }
                    } else {
                        errors.push(`Invalid ID for user: ${users[i].id}`);
                    }
                } else {
                    errors.push(`Missing required properties for user: ${JSON.stringify(users[i])}`);
                }
            } else {
                errors.push(`Invalid user data type at index ${i}: ${typeof users[i]}`);
            }
        } else {
            errors.push(`Null or undefined user at index ${i}`);
        }
    }
    
    return { results, errors };
}

// Duplicate code - similar validation logic repeated
function validateUserData(users) {
    let validUsers = [];
    
    for (let i = 0; i < users.length; i++) {
        if (users[i] !== null && users[i] !== undefined) {
            if (typeof users[i] === 'object') {
                if (users[i].hasOwnProperty('id') && users[i].hasOwnProperty('name')) {
                    if (users[i].id > 0) {
                        if (users[i].name && users[i].name.length > 0) {
                            validUsers.push(users[i]);
                        }
                    }
                }
            }
        }
    }
    
    return validUsers;
}

// Function without proper error handling
function fetchDataFromAPI(url) {
    return axios.get(url)
        .then(response => response.data)
        .catch(error => {
            console.log('Error occurred:', error.message);
            return null;
        });
}

// Function with too many parameters
function createUserReport(userId, userName, userEmail, userAge, userAddress, userPhone, userJob, userSalary, userDepartment, includePersonalInfo, includeWorkInfo, formatType, outputPath) {
    // Implementation with many parameters - should use options object
    let report = {
        id: userId,
        name: userName
    };
    
    if (includePersonalInfo) {
        report.email = userEmail;
        report.age = userAge;
        report.address = userAddress;
        report.phone = userPhone;
    }
    
    if (includeWorkInfo) {
        report.job = userJob;
        report.salary = userSalary;
        report.department = userDepartment;
    }
    
    // Long line that should be broken down for better readability and maintainability
    let formattedReport = formatType === 'json' ? JSON.stringify(report, null, 2) : formatType === 'csv' ? convertToCSV(report) : formatType === 'xml' ? convertToXML(report) : report.toString();
    
    if (outputPath) {
        fs.writeFileSync(outputPath, formattedReport);
    }
    
    return formattedReport;
}

// Missing function implementations (referenced but not defined)
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function convertToCSV(data) {
    // Stub implementation
    return Object.entries(data).map(([key, value]) => `${key},${value}`).join('\n');
}

function convertToXML(data) {
    // Stub implementation
    let xml = '<user>\n';
    for (let [key, value] of Object.entries(data)) {
        xml += `  <${key}>${value}</${key}>\n`;
    }
    xml += '</user>';
    return xml;
}

// Unused function - dead code
function unusedUtilityFunction() {
    console.log('This function is never called');
    return 'unused';
}

// Export everything - should be more selective
module.exports = {
    processUserData,
    validateUserData,
    fetchDataFromAPI,
    createUserReport,
    validateEmail,
    convertToCSV,
    convertToXML,
    unusedUtilityFunction,
    globalCounter,
    sharedData
};