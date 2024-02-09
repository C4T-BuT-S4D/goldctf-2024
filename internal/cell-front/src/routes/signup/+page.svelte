<script>
    import {invalidateAll, goto} from '$app/navigation';
    import Person from 'svelte-ionicons/Person.svelte';
    import LockClosed from 'svelte-ionicons/LockClosed.svelte';
    import {PUBLIC_BASE_URL} from "$env/static/public";
    import { userData } from '$lib/storage.js';

      /** @type {any} */
    let error;

    /** @param {{ currentTarget: EventTarget & HTMLFormElement}} event */
    async function handleSubmit(event) {
        const data = new FormData(event.currentTarget);

        let username = data.get('username');
        let password = data.get('password');

        try {
            const res = await fetch(`${PUBLIC_BASE_URL}/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({login: username, password: password})
            });
            if (res.ok) {
                let response = await res.json();
                let udata = {"uid": response.data.uid, "username": response.data.username};
                userData.update(user => udata);
                await goto('/', {invalidateAll: true});
                return;
            }
            error = await res.text();
            try {
                error = JSON.parse(error).data.error;
            } catch (err) {
                // ignore
            }
        } catch (err) {
            error = err.toString();
        }
        await invalidateAll();
    }
</script>
<section class="section">
    {#if error}
        <div class="container">
            <div class="notification is-danger">
                {error}
            </div>
        </div>
    {/if}
</section>
<section class="section">
    <div class="columns is-centered">
        <div class="column is-half has-text-centered">
            <p class="is-size-4">Let's signup.</p>
        </div>
    </div>
    <div class="columns is-centered">
        <div class="column is-half has-text-centered">
            <form  on:submit|preventDefault={handleSubmit}>
                <div class="field">
                    <p class="control has-icons-left has-icons-right">
                        <input class="input" name="username" type="text" placeholder="Username">
                        <span class="icon is-small is-left">
                            <Person />
                        </span>
                    </p>
                </div>
                <div class="field">
                    <p class="control has-icons-left">
                        <input class="input" name="password" type="password" placeholder="Password">
                        <span class="icon is-small is-left">
                            <LockClosed />
                        </span>
                    </p>
                </div>
                <div class="field">
                    <p class="control">
                        <input type="submit" value="SignUp" class="button is-success">
                    </p>
                </div>
            </form>
        </div>
    </div>
</section>