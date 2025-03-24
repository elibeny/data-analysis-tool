// Firebase references
const storage = firebase.storage();
const functions = firebase.functions();

// Vue app
const { createApp } = Vue;

const app = createApp({
    delimiters: ['${', '}'],  // Use different delimiters to avoid conflict with Jinja
    data() {
        return {
            dataframes: {},
            wordFrequencyData: []
        }
    },
    methods: {
        // Navigation methods
        selectProject(projectType) {
            document.getElementById('projectSelection').style.display = 'none';
            document.getElementById(projectType).style.display = 'block';
        },
        
        goBackToSelection() {
            document.querySelectorAll('.project-section').forEach(section => {
                section.style.display = 'none';
            });
            document.getElementById('projectSelection').style.display = 'block';
            return false;  // Prevent default anchor behavior
        },
        
        // Data handling methods
        downloadData(url, filename) {
            fetch(url)
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                })
                .catch(error => {
                    console.error('Download error:', error);
                    alert('Failed to download the file. Please try again.');
                });
        },
        
        // Form submission handlers
        async uploadAndProcess(e) {
            document.querySelector('.loading').style.display = 'flex';
            
            const fileInput = document.getElementById('file');
            if (!fileInput.files[0]) {
                alert('Please select a file to upload');
                document.querySelector('.loading').style.display = 'none';
                return;
            }
            
            try {
                // Upload the file to Firebase Storage first
                const storageRef = storage.ref();
                const fileRef = storageRef.child(`uploads/${fileInput.files[0].name}`);
                
                await fileRef.put(fileInput.files[0]);
                const downloadURL = await fileRef.getDownloadURL();
                
                // Call the Cloud Function with the file URL
                const apiFunction = functions.httpsCallable('api');
                const result = await apiFunction({
                    endpoint: '/scaling',
                    fileUrl: downloadURL,
                    fileName: fileInput.files[0].name
                });
                
                const data = result.data;
                
                if (data.success) {
                    document.getElementById('scalingSummary').textContent = data.summary;
                    
                    this.dataframes = data.dataframes;  // Update Vue data
                    
                    document.getElementById('scalingResults').style.display = 'block';
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while processing your request.');
            } finally {
                document.querySelector('.loading').style.display = 'none';
            }
        },
        
        async analyzeText(e) {
            const text = document.getElementById('text').value;
            if (!text.trim()) {
                alert('Please enter some text to analyze');
                return;
            }
            
            document.querySelector('.loading').style.display = 'flex';
            
            try {
                // Call the Firebase Cloud Function
                const apiFunction = functions.httpsCallable('api');
                
                const result = await apiFunction({
                    endpoint: '/word-frequency',
                    text: text
                });
                
                const data = result.data;
                
                if (data.success) {
                    // Display results
                    this.wordFrequencyData = data.results;
                    
                    // Create a bar chart with Plotly
                    const words = this.wordFrequencyData.map(item => item.word);
                    const counts = this.wordFrequencyData.map(item => item.count);
                    
                    const chartData = [{
                        x: words,
                        y: counts,
                        type: 'bar',
                        marker: {
                            color: '#4361ee'
                        }
                    }];
                    
                    const layout = {
                        title: 'Word Frequency Analysis',
                        xaxis: {
                            title: 'Words'
                        },
                        yaxis: {
                            title: 'Frequency'
                        },
                        responsive: true
                    };
                    
                    Plotly.newPlot('wordFrequencyChart', chartData, layout);
                    
                    document.getElementById('wordCounterResults').style.display = 'block';
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while processing your request.');
            } finally {
                document.querySelector('.loading').style.display = 'none';
            }
        },
        
        downloadWordFrequencyResults() {
            if (!this.wordFrequencyData || this.wordFrequencyData.length === 0) {
                alert('No data to download. Please analyze text first.');
                return;
            }
            
            let csvContent = "data:text/csv;charset=utf-8,Word,Frequency\n";
            
            this.wordFrequencyData.forEach(item => {
                csvContent += `${item.word},${item.count}\n`;
            });
            
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "word_frequency.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
}).mount('#app');

// Initialize UI elements on page load
document.addEventListener('DOMContentLoaded', function() {
    // Hide all project sections initially
    document.querySelectorAll('.project-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show project selection
    document.getElementById('projectSelection').style.display = 'block';
});
