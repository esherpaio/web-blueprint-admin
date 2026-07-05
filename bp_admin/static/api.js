async function callApi(method, url, data = null, contentType = null, silent = false) {
    if (data && method === "GET") {
        url = `${url}?${new URLSearchParams(data)}`;
        data = null;
    } else if (data && contentType === "application/json") {
        data = JSON.stringify(data);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    const options = { body: data, method: method, signal: controller.signal };
    if (contentType) {
        options.headers = { "Content-Type": contentType };
    }

    let resp;
    try {
        const response = await fetch(url, options);
        resp = await response.json();
    } catch {
        resp = undefined;
    } finally {
        clearTimeout(timeoutId);
    }

    if (resp && resp.code >= 200 && resp.code <= 299) {
        return resp;
    }
    if (silent) {
        return resp;
    }
    throw new Error((resp && resp.message) || "Something went wrong on our end.");
}
