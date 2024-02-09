<script>
    import { onMount } from 'svelte';
    import spreadsheet from '$lib/images/spreadsheet.png';
    import {PUBLIC_BASE_URL} from '$env/static/public';
    export let sheets = [];

    onMount(async () => {
        const response = await fetch(`${PUBLIC_BASE_URL}/sheets`, {credentials: 'include'});
        const data = await response.json();
        console.log(data);
        sheets = data;
    });
</script>
<div>
    <img width="64" src={spreadsheet} alt="spreadsheet" />
    <p>Sheets created by you:</p>
    <div class="content is-medium has-text-centered">
        {#each sheets as sheet}
            <p><a href="/sheet/{sheet.sid}?readToken={sheet.readToken}&writeToken={sheet.modifyToken}">{sheet.title}</a></p>
        {/each}
    </div>

</div>
