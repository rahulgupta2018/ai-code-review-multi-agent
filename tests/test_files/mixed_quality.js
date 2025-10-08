
// Mixed quality JavaScript code for testing
class DataProcessor {
    constructor() {
        this.data = [];
        this.processed = false;
    }
    
    // Good: Well-documented function
    /**
     * Processes data with validation
     * @param {Array} inputData - The data to process
     * @returns {Object} Processing result
     */
    processData(inputData) {
        if (!Array.isArray(inputData)) {
            throw new Error('Input must be an array');
        }
        
        this.data = inputData.filter(item => item !== null);
        this.processed = true;
        
        return {
            count: this.data.length,
            processed: this.processed
        };
    }
    
    // Poor: Deeply nested and no documentation
    analyzeComplexData(data) {
        if (data) {
            if (data.length > 0) {
                if (data[0]) {
                    if (data[0].type === 'complex') {
                        if (data[0].values) {
                            if (data[0].values.length > 10) {
                                let result = 0;
                                for (let i = 0; i < data[0].values.length; i++) {
                                    if (data[0].values[i] > 0) {
                                        result += data[0].values[i] * 2;
                                    }
                                }
                                return result;
                            }
                        }
                    }
                }
            }
        }
        return 0;
    }
}
