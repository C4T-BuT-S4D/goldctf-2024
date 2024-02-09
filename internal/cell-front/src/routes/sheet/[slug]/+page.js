import {PUBLIC_BASE_URL} from '$env/static/public';

export async function load({fetch,  parent, params, url}) {
    let slug = params.slug;
    let readToken = url.searchParams.get('readToken');
    let writeToken = url.searchParams.get('writeToken');

    if (readToken === null) {
        let error = "No read token provided";
        return {sheet: {}, error: error};
    }
    
    let searchParams = new URLSearchParams();
    searchParams.append('token', readToken);
    

    let sheetURL = `${PUBLIC_BASE_URL}/sheets/${slug}?${searchParams.toString()}`;

    let res = await fetch(sheetURL, {
        credentials: 'include'
    });

    if (res.ok) {
        let sheetData = await res.json();
        return {sheet: {
            data: sheetData,
            id: slug,
            tokens: {
                read: readToken,
                write: writeToken
            }
        }, error: null};
    }

    let error = await res.text();
    try {
        error = await res.json().data.error;
    } catch (e) {
        // ignore.
    }


    return {sheet: {}, error: error};
}