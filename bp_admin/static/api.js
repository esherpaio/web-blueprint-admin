async function callApi(method, url, data = null, contentType = null, silent = false) {
    if (data && method === "GET") {
        let url_params = "?";
        for (const [key, value] of Object.entries(data)) {
            url_params += `${key}=${value}`;
        }
        url = `${url}${url_params}`;
        data = null;
    } else if (data && contentType === "application/json") {
        data = JSON.stringify(data);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000);
    let options = {
        body: data,
        headers: { "Content-Type": contentType },
        method: method,
        signal: controller.signal,
    };
    if (contentType === false) {
        delete options.headers;
    }

    let resp;
    return await fetch(url, options)
        .then((data) => {
            return data.json();
        })
        .then((data) => {
            clearTimeout(timeoutId);
            resp = data;
            console.info(`API ${method} ${resp.code} ${url}`);
            if (200 <= resp.code && resp.code <= 299) {
                return resp;
            } else {
                return Promise.reject();
            }
        })
        .catch(() => {
            let message, error;
            if (resp && resp.message) {
                message = resp.message;
                error = resp.message;
            } else {
                message = "Something went wrong on our end.";
                error = "No response from API.";
            }
            if (!silent) {
                resetButtons();
                showMessage(message);
                throw new Error(error);
            } else {
                return resp;
            }
        });
}

function emptyStrToNull(dict) {
    for (let key in dict) {
        if (dict[key] === "") {
            dict[key] = null;
        }
    }
    return dict;
}
