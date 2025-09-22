document.addEventListener('DOMContentLoaded', () => {
    const loginContainer = document.getElementById('login-container');
    const dataContainer = document.getElementById('data-container');
    const businessInfoDiv = document.getElementById('business-info');
    const loader = document.getElementById('loader');

    // Function to fetch and display business data
    const fetchBusinessData = async () => {
        try {
            const response = await fetch('/api/get-business-data');

            // If the response is 401, it means the user is not authenticated
            if (response.status === 401) {
                loginContainer.classList.remove('hidden');
                dataContainer.classList.add('hidden');
                return;
            }

            // If we get here, the user is logged in
            loginContainer.classList.add('hidden');
            dataContainer.classList.remove('hidden');

            const data = await response.json();
            loader.classList.add('hidden'); // Hide loader once data is fetched

            if (data.error) {
                businessInfoDiv.innerHTML = `<p>Error: ${data.error}</p>`;
                return;
            }

            if (data.locations && data.locations.length > 0) {
                // Clear previous data
                businessInfoDiv.innerHTML = '';
                // Create a card for each location
                data.locations.forEach(location => {
                    const card = document.createElement('div');
                    card.className = 'location-card';
                    card.innerHTML = `
                        <h3>${location.title || 'No Title'}</h3>
                        <p><strong>Address:</strong> ${location.address?.addressLines?.join(', ') || 'N/A'}</p>
                        <p><strong>Phone:</strong> ${location.phoneNumbers?.primaryPhone || 'N/A'}</p>
                    `;
                    businessInfoDiv.appendChild(card);
                });
            } else {
                businessInfoDiv.innerHTML = '<p>No locations found in your account.</p>';
            }

        } catch (error) {
            console.error('Failed to fetch data:', error);
            businessInfoDiv.innerHTML = '<p>Failed to load data. Please try again.</p>';
        }
    };

    // Call the function to check login status and fetch data when the page loads
    fetchBusinessData();
});