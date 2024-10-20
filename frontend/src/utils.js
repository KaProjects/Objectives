import {properties} from "@/properties";
import {app_state} from "@/main";

export function backend_fetch(path, requestOptions = null) {
    return fetch("http://" + properties.backend_host + ":" + properties.backend_port + path, requestOptions)
        .then(async response => {
            if (response.ok) {
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    return await response.json()
                } else {
                    return await response.text()
                }
            } else {
                app_state.handle_fetch_error("[" + response.status + "] " + await response.text())
            }})
        .catch(error => app_state.handle_fetch_error(error))
}
export function backend_get(path) {
    const requestOptions = {
        method: "GET",
        headers: {"Authorization": "Bearer " + app_state.token},
    }
    return backend_fetch(path, requestOptions)
}
export function backend_delete(path) {
    const requestOptions = {
        method: "DELETE",
        headers: {"Authorization": "Bearer " + app_state.token},
    }
    return backend_fetch(path, requestOptions)
}
export function backend_post(path, data) {
    const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json", "Authorization": "Bearer " + app_state.token},
        body: JSON.stringify(data)
    }
    return backend_fetch(path, requestOptions)
}
export function backend_put(path, data) {
    const requestOptions = {
        method: "PUT",
        headers: {"Content-Type": "application/json", "Authorization": "Bearer " + app_state.token},
        body: JSON.stringify(data)
    }
    return backend_fetch(path, requestOptions)
}
export function string_to_html(string){
    let urls = string.match(/https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)/g)
    if (urls !== null) {
        for (let url of urls){
            let text;
            const subUrl = url.split("\/\/")[1]
            if (url.includes("docs.google.com")){
                text = "google-" + subUrl.split("\/")[1]
            } else if (url.includes("trello.com")){
                text = "trello-" + subUrl.split("\/").pop()
            } else if (url.includes("github.com")){
                text = "gh-" + subUrl.split("\/")[1] + "-" + subUrl.split("\/")[2]
            } else {
                text = url.split("\/\/")[1].split("\/")[0]
            }
            string = string.replace(url, "<a href=\"" + url + "\" target=\"_blank\" onclick=\"event.cancelBubble=true;\">" + text + "</a>")
        }
    }

    string = string.replaceAll('\n', "<br>")

    let bolds = string.match(/\*[^*]*\*/g)
    if (bolds !== null) {
        for (let bold of bolds){
            string = string.replace(bold, bold.replace("*","<b>").replace("*","</b>"))
        }
    }

    let strikes = string.match(/\^[^*]*\^/g)
    if (strikes !== null) {
        for (let strike of strikes){
            string = string.replace(strike, strike.replace("^","<s>").replace("^","</s>"))
        }
    }

    return string
}
export function compare_dates(a, b){
    let dateA = a.split("/")
    let dateB = b.split("/")
    if (dateA[2] !== dateB[2]){
        return parseInt(dateA[2]) - parseInt(dateB[2])
    } else {
        if (dateA[1] !== dateB[1]) {
            return parseInt(dateA[1]) - parseInt(dateB[1])
        } else {
            if (dateA[0] !== dateB[0]) {
                return parseInt(dateA[0]) - parseInt(dateB[0])
            } else {
                return 0
            }
        }
    }
}