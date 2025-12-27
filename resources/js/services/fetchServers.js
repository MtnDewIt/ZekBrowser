const API_ENDPOINT = 'http://localhost:8000/api/';

export function fetchServers() {
    return new Promise((resolve, reject) => {
        fetch(API_ENDPOINT)
            .then((response) => response.json())
            .then(resolve)
            .catch(reject);
    });
}
