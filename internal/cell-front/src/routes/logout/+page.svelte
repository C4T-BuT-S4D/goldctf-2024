<script>
    import {invalidateAll, goto} from '$app/navigation';
    import {PUBLIC_BASE_URL} from "$env/static/public";
    import { userData } from '$lib/storage.js';

    function logout() {
        fetch(`${PUBLIC_BASE_URL}/logout`, {
            method: 'POST',
            credentials: 'include',
        }).then(() => {
            userData.update(user => ({
                username: null,
                uid: null,
            }));
            invalidateAll();
            goto('/');
        });
    }
</script>

<nav class="level">
    <div class="level-item has-text-centered">
        <div>
            Are you sure you want to log out?
        </div>
    </div>
    <div class="level-item has-text-centered">
        <div>
            <a class="button is-medium is-primary" on:click={logout}>Logout</a>
        </div>
    </div>
</nav>