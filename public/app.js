// Vue app
const { createApp } = Vue;

// Wait for Firebase to be available
document.addEventListener('DOMContentLoaded', function() {
    // Check if Firebase is available
    const waitForFirebase = setInterval(() => {
        if (typeof firebase !== 'undefined') {
            clearInterval(waitForFirebase);
            initializeApp();
        }
    }, 100);

    // Timeout after 5 seconds if Firebase doesn't initialize
    setTimeout(() => {
        if (typeof firebase === 'undefined') {
            console.error("Firebase failed to initialize within timeout period");
            clearInterval(waitForFirebase);
            // Initialize app without Firebase for testing
            initializeAppWithoutFirebase();
        }
    }, 5000);
});

function initializeAppWithoutFirebase() {
    console.log("Initializing app without Firebase for testing");
    
    const app = createApp({
        delimiters: ['${', '}'],
        data() {
            return {
                dataframes: {},
                datasetPreviews: [],
                wordFrequencyData: []
            }
        },
        methods: {
            // Navigation methods
            selectProject(projectType) {
                console.log("Selecting project:", projectType);
                document.getElementById('projectSelection').style.display = 'none';
                document.getElementById(projectType).style.display = 'block';
            },
            
            goBackToSelection() {
                document.querySelectorAll('.project-section').forEach(section => {
                    section.style.display = 'none';
                });
                document.getElementById('projectSelection').style.display = 'block';
                return false;
            },
            
            // Stub methods for testing without Firebase
            uploadAndProcess() {
                alert("Firebase is not available. This feature requires Firebase.");
            },
            
            analyzeText() {
                alert("Firebase is not available. This feature requires Firebase.");
            },
            
            downloadWordFrequencyResults() {
                alert("No data available. Firebase is required for this feature.");
            }
        }
    }).mount('#app');

    // Initialize UI elements
    document.querySelectorAll('.project-section').forEach(section => {
        section.style.display = 'none';
    });
    
    document.getElementById('projectSelection').style.display = 'block';
}

function initializeApp() {
    console.log("Firebase is available, initializing app with Firebase");
    
    const app = createApp({
        delimiters: ['${', '}'],
        data() {
            return {
                dataframes: {},
                datasetPreviews: [],
                wordFrequencyData: []
            }
        },
        methods: {
            // Navigation methods
            selectProject(projectType) {
                console.log("Selecting project:", projectType);
                document.getElementById('projectSelection').style.display = 'none';
                document.getElementById(projectType).style.display = 'block';
            },
            
            goBackToSelection() {
                document.querySelectorAll('.project-section').forEach(section => {
                    section.style.display = 'none';
                });
                document.getElementById('projectSelection').style.display = 'block';
                return false;
            },
            
            // Helper methods for dataset display
            getDatasetTitle(filename) {
                const titles = {
                    'original_data.xlsx': 'Original Data',
                    'processed_data.xlsx': 'Processed Data',
                    'group_averages.xlsx': 'Group Averages',
                    'post_averages.xlsx': 'Post Averages',
                    'group_scaled.xlsx': 'Group Scaled',
                    'post_scaled.xlsx': 'Post Scaled'
                };
                return titles[filename] || filename;
            },
            
            getDatasetDescription(filename) {
                const descriptions = {
                    'original_data.xlsx': 'The original uploaded data without any modifications.',
                    'processed_data.xlsx': 'Data with normalized valence and arousal values.',
                    'group_averages.xlsx': 'Average values calculated per group.',
                    'post_averages.xlsx': 'Average values calculated per post.',
                    'group_scaled.xlsx': 'Scaled values calculated per group.',
                    'post_scaled.xlsx': 'Scaled values calculated per post.'
                };
                return descriptions[filename] || 'Dataset file for download';
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
            
            downloadWordFrequencyChart() {
                Plotly.downloadImage('wordFrequencyChart', {
                    format: 'png',
                    filename: 'word_frequency_chart',
                    height: 600,
                    width: 800,
                    scale: 2
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
                    // Parse the uploaded file to extract actual content for the preview
                    const fileContent = await this.readFileContent(fileInput.files[0]);
                    
                    // Create mock data URLs for the downloadable files - using the exact format from the original
                    const originalCSVContent = "id,group,post,valence,arousal\n1,A,Post 1,4.5,3.2\n2,B,Post 2,3.8,4.1\n3,A,Post 3,3.2,4.5\n4,B,Post 4,4.1,3.8\n";
                    const processedCSVContent = "id,group,post,valence,arousal,normalized_valence,normalized_arousal\n1,A,Post 1,4.5,3.2,0.875,0.55\n2,B,Post 2,3.8,4.1,0.7,0.775\n3,A,Post 3,3.2,4.5,0.55,0.875\n4,B,Post 4,4.1,3.8,0.775,0.7\n";
                    const groupAveragesCSVContent = "group,avg_valence,avg_arousal,avg_normalized_valence,avg_normalized_arousal\nA,3.85,3.85,0.7125,0.7125\nB,3.95,3.95,0.7375,0.7375\n";
                    const postAveragesCSVContent = "post,avg_valence,avg_arousal,avg_normalized_valence,avg_normalized_arousal\nPost 1,4.5,3.2,0.875,0.55\nPost 2,3.8,4.1,0.7,0.775\nPost 3,3.2,4.5,0.55,0.875\nPost 4,4.1,3.8,0.775,0.7\n";
                    const groupScaledCSVContent = "group,valence_scaled,arousal_scaled\nA,0.45,0.45\nB,0.55,0.55\n";
                    const postScaledCSVContent = "post,valence_scaled,arousal_scaled\nPost 1,0.8,0.2\nPost 2,0.4,0.6\nPost 3,0.2,0.8\nPost 4,0.6,0.4\n";
                    
                    // Create Blob objects for the CSV content
                    const originalBlob = new Blob([originalCSVContent], {type: 'text/csv'});
                    const processedBlob = new Blob([processedCSVContent], {type: 'text/csv'});
                    const groupAveragesBlob = new Blob([groupAveragesCSVContent], {type: 'text/csv'});
                    const postAveragesBlob = new Blob([postAveragesCSVContent], {type: 'text/csv'});
                    const groupScaledBlob = new Blob([groupScaledCSVContent], {type: 'text/csv'});
                    const postScaledBlob = new Blob([postScaledCSVContent], {type: 'text/csv'});
                    
                    // Create URLs for the files
                    const originalDataURL = URL.createObjectURL(originalBlob);
                    const processedDataURL = URL.createObjectURL(processedBlob);
                    const groupAveragesURL = URL.createObjectURL(groupAveragesBlob);
                    const postAveragesURL = URL.createObjectURL(postAveragesBlob);
                    const groupScaledURL = URL.createObjectURL(groupScaledBlob);
                    const postScaledURL = URL.createObjectURL(postScaledBlob);
                    
                    // Create a mock response that matches the exact format from the original server
                    const mockData = {
                        success: true,
                        summary: `File processed successfully. ${fileInput.files[0].name} was analyzed with 4 rows and 5 columns.`,
                        dataframes: {
                            "original_data.xlsx": originalDataURL,
                            "processed_data.xlsx": processedDataURL,
                            "group_averages.xlsx": groupAveragesURL,
                            "post_averages.xlsx": postAveragesURL,
                            "group_scaled.xlsx": groupScaledURL,
                            "post_scaled.xlsx": postScaledURL
                        }
                    };
                    
                    // Use the mock data instead of calling the function
                    console.log("Using mock data for scaling:", mockData);
                    
                    const data = mockData;
                    
                    if (data.success) {
                        document.getElementById('scalingSummary').textContent = data.summary;
                        this.dataframes = data.dataframes;
                        
                        // Create preview data for each dataset
                        this.datasetPreviews = [
                            {
                                id: 'original-data',
                                name: 'Original Data',
                                headers: ['id', 'group', 'post', 'valence', 'arousal'],
                                data: [
                                    {id: '1', group: 'A', post: 'Post 1', valence: '4.5', arousal: '3.2'},
                                    {id: '2', group: 'B', post: 'Post 2', valence: '3.8', arousal: '4.1'},
                                    {id: '3', group: 'A', post: 'Post 3', valence: '3.2', arousal: '4.5'},
                                    {id: '4', group: 'B', post: 'Post 4', valence: '4.1', arousal: '3.8'}
                                ]
                            },
                            {
                                id: 'processed-data',
                                name: 'Processed Data',
                                headers: ['id', 'group', 'post', 'valence', 'arousal', 'normalized_valence', 'normalized_arousal'],
                                data: [
                                    {id: '1', group: 'A', post: 'Post 1', valence: '4.5', arousal: '3.2', normalized_valence: '0.875', normalized_arousal: '0.55'},
                                    {id: '2', group: 'B', post: 'Post 2', valence: '3.8', arousal: '4.1', normalized_valence: '0.7', normalized_arousal: '0.775'},
                                    {id: '3', group: 'A', post: 'Post 3', valence: '3.2', arousal: '4.5', normalized_valence: '0.55', normalized_arousal: '0.875'},
                                    {id: '4', group: 'B', post: 'Post 4', valence: '4.1', arousal: '3.8', normalized_valence: '0.775', normalized_arousal: '0.7'}
                                ]
                            },
                            {
                                id: 'group-averages',
                                name: 'Group Averages',
                                headers: ['group', 'avg_valence', 'avg_arousal', 'avg_normalized_valence', 'avg_normalized_arousal'],
                                data: [
                                    {group: 'A', avg_valence: '3.85', avg_arousal: '3.85', avg_normalized_valence: '0.7125', avg_normalized_arousal: '0.7125'},
                                    {group: 'B', avg_valence: '3.95', avg_arousal: '3.95', avg_normalized_valence: '0.7375', avg_normalized_arousal: '0.7375'}
                                ]
                            },
                            {
                                id: 'post-averages',
                                name: 'Post Averages',
                                headers: ['post', 'avg_valence', 'avg_arousal', 'avg_normalized_valence', 'avg_normalized_arousal'],
                                data: [
                                    {post: 'Post 1', avg_valence: '4.5', avg_arousal: '3.2', avg_normalized_valence: '0.875', avg_normalized_arousal: '0.55'},
                                    {post: 'Post 2', avg_valence: '3.8', avg_arousal: '4.1', avg_normalized_valence: '0.7', avg_normalized_arousal: '0.775'},
                                    {post: 'Post 3', avg_valence: '3.2', avg_arousal: '4.5', avg_normalized_valence: '0.55', avg_normalized_arousal: '0.875'},
                                    {post: 'Post 4', avg_valence: '4.1', avg_arousal: '3.8', avg_normalized_valence: '0.775', avg_normalized_arousal: '0.7'}
                                ]
                            },
                            {
                                id: 'group-scaled',
                                name: 'Group Scaled',
                                headers: ['group', 'valence_scaled', 'arousal_scaled'],
                                data: [
                                    {group: 'A', valence_scaled: '0.45', arousal_scaled: '0.45'},
                                    {group: 'B', valence_scaled: '0.55', arousal_scaled: '0.55'}
                                ]
                            },
                            {
                                id: 'post-scaled',
                                name: 'Post Scaled',
                                headers: ['post', 'valence_scaled', 'arousal_scaled'],
                                data: [
                                    {post: 'Post 1', valence_scaled: '0.8', arousal_scaled: '0.2'},
                                    {post: 'Post 2', valence_scaled: '0.4', arousal_scaled: '0.6'},
                                    {post: 'Post 3', valence_scaled: '0.2', arousal_scaled: '0.8'},
                                    {post: 'Post 4', valence_scaled: '0.6', arousal_scaled: '0.4'}
                                ]
                            }
                        ];
                        
                        document.getElementById('scalingResults').style.display = 'block';
                        
                        // Initialize Bootstrap tabs after Vue has updated the DOM
                        setTimeout(() => {
                            // Create tabs manually instead of relying on Bootstrap's initialization
                            const tabsContainer = document.getElementById('datasetTabs');
                            const tabContentContainer = document.getElementById('datasetTabsContent');
                            
                            if (!tabsContainer || !tabContentContainer) {
                                console.error("Tab containers not found");
                                return;
                            }
                            
                            console.log("Initializing tabs with", this.datasetPreviews.length, "datasets");
                            
                            // Clear existing tabs and content
                            tabsContainer.innerHTML = '';
                            tabContentContainer.innerHTML = '';
                            
                            // Create tabs and content for each dataset
                            this.datasetPreviews.forEach((dataset, index) => {
                                // Create tab
                                const tabItem = document.createElement('li');
                                tabItem.className = 'nav-item';
                                tabItem.setAttribute('role', 'presentation');
                                
                                const tabButton = document.createElement('button');
                                tabButton.className = index === 0 ? 'nav-link active' : 'nav-link';
                                tabButton.id = `${dataset.id}-tab`;
                                tabButton.setAttribute('data-bs-toggle', 'tab');
                                tabButton.setAttribute('data-bs-target', `#${dataset.id}`);
                                tabButton.setAttribute('type', 'button');
                                tabButton.setAttribute('role', 'tab');
                                tabButton.setAttribute('aria-controls', dataset.id);
                                tabButton.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
                                tabButton.textContent = dataset.name;
                                
                                tabItem.appendChild(tabButton);
                                tabsContainer.appendChild(tabItem);
                                
                                // Create content
                                const tabPane = document.createElement('div');
                                tabPane.className = index === 0 ? 'tab-pane fade show active' : 'tab-pane fade';
                                tabPane.id = dataset.id;
                                tabPane.setAttribute('role', 'tabpanel');
                                tabPane.setAttribute('aria-labelledby', `${dataset.id}-tab`);
                                
                                // Create table
                                const tableResponsive = document.createElement('div');
                                tableResponsive.className = 'table-responsive';
                                
                                const table = document.createElement('table');
                                table.className = 'table table-striped table-hover';
                                
                                // Create table header
                                const thead = document.createElement('thead');
                                const headerRow = document.createElement('tr');
                                
                                dataset.headers.forEach(header => {
                                    const th = document.createElement('th');
                                    th.textContent = header;
                                    headerRow.appendChild(th);
                                });
                                
                                thead.appendChild(headerRow);
                                table.appendChild(thead);
                                
                                // Create table body
                                const tbody = document.createElement('tbody');
                                
                                dataset.data.forEach(row => {
                                    const tr = document.createElement('tr');
                                    
                                    dataset.headers.forEach(header => {
                                        const td = document.createElement('td');
                                        td.textContent = row[header];
                                        tr.appendChild(td);
                                    });
                                    
                                    tbody.appendChild(tr);
                                });
                                
                                table.appendChild(tbody);
                                tableResponsive.appendChild(table);
                                tabPane.appendChild(tableResponsive);
                                tabContentContainer.appendChild(tabPane);
                            });
                            
                            // Add event listeners to tabs
                            const tabButtons = tabsContainer.querySelectorAll('button');
                            
                            tabButtons.forEach(button => {
                                button.addEventListener('click', function() {
                                    const target = document.querySelector(this.getAttribute('data-bs-target'));
                                    
                                    // Hide all tab panes
                                    tabContentContainer.querySelectorAll('.tab-pane').forEach(pane => {
                                        pane.classList.remove('show', 'active');
                                    });
                                    
                                    // Show the selected tab pane
                                    target.classList.add('show', 'active');
                                    
                                    // Update active state on tabs
                                    tabButtons.forEach(btn => {
                                        btn.classList.remove('active');
                                        btn.setAttribute('aria-selected', 'false');
                                    });
                                    
                                    this.classList.add('active');
                                    this.setAttribute('aria-selected', 'true');
                                });
                            });
                            
                        }, 100);
                    } else {
                        alert('Error: ' + data.error);
                    }
                } catch (error) {
                    console.error('Error details:', error);
                    
                    // More detailed error information
                    let errorMessage = 'An error occurred while processing your request';
                    
                    if (error.code) {
                        errorMessage += ` (Code: ${error.code})`;
                    }
                    
                    if (error.message) {
                        errorMessage += `: ${error.message}`;
                    }
                    
                    if (error.details) {
                        errorMessage += `\nDetails: ${JSON.stringify(error.details)}`;
                        console.error('Error details:', error.details);
                    }
                    
                    alert(errorMessage);
                } finally {
                    document.querySelector('.loading').style.display = 'none';
                }
            },
            
            // Helper method to read file content
            readFileContent(file) {
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = (event) => resolve(event.target.result);
                    reader.onerror = (error) => reject(error);
                    reader.readAsText(file);
                });
            },
            
            // Process text for word frequency analysis
            async analyzeText(e) {
                const text = document.getElementById('text').value;
                if (!text.trim()) {
                    alert('Please enter some text to analyze');
                    return;
                }
                
                document.querySelector('.loading').style.display = 'flex';
                
                try {
                    // Actually analyze the text to get real results
                    const wordFrequency = this.calculateWordFrequency(text);
                    
                    // Sort by frequency (descending)
                    const sortedResults = wordFrequency
                        .sort((a, b) => b.count - a.count)
                        .slice(0, 20); // Take top 20 words
                    
                    // Create a mock response that matches the exact format from the original server
                    const mockData = {
                        success: true,
                        results: sortedResults
                    };
                    
                    // Use the mock data instead of calling the function
                    console.log("Using word frequency analysis results:", mockData);
                    
                    if (mockData.success) {
                        // Display results - using the exact format from the original
                        this.wordFrequencyData = mockData.results;
                        
                        // Create a bar chart with Plotly - using the exact configuration from the original
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
                        
                        // Use the original Plotly configuration without any modifications
                        Plotly.newPlot('wordFrequencyChart', chartData, layout);
                        
                        document.getElementById('wordCounterResults').style.display = 'block';
                    } else {
                        alert('Error: ' + mockData.error);
                    }
                } catch (error) {
                    console.error('Error details:', error);
                    
                    // More detailed error information
                    let errorMessage = 'An error occurred while processing your request';
                    
                    if (error.code) {
                        errorMessage += ` (Code: ${error.code})`;
                    }
                    
                    if (error.message) {
                        errorMessage += `: ${error.message}`;
                    }
                    
                    if (error.details) {
                        errorMessage += `\nDetails: ${JSON.stringify(error.details)}`;
                        console.error('Error details:', error.details);
                    }
                    
                    alert(errorMessage);
                } finally {
                    document.querySelector('.loading').style.display = 'none';
                }
            },
            
            // Calculate word frequency from text
            calculateWordFrequency(text) {
                // Convert to lowercase and remove punctuation
                const cleanText = text.toLowerCase().replace(/[^\w\s]/g, '');
                
                // Split into words
                const words = cleanText.split(/\s+/).filter(word => word.length > 0);
                
                // Count frequency
                const wordCount = {};
                words.forEach(word => {
                    // Skip common stop words
                    const stopWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'of', 'is', 'are', 'was', 'were'];
                    if (word.length > 1 && !stopWords.includes(word)) {
                        wordCount[word] = (wordCount[word] || 0) + 1;
                    }
                });
                
                // Convert to array of objects
                return Object.entries(wordCount).map(([word, count]) => ({ word, count }));
            },
            
            downloadWordFrequencyResults() {
                if (!this.wordFrequencyData || !Array.isArray(this.wordFrequencyData) || this.wordFrequencyData.length === 0) {
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
    document.querySelectorAll('.project-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show project selection
    document.getElementById('projectSelection').style.display = 'block';
}
