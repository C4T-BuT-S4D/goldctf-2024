/** @type {import('./$types').PageLoad} */
import { PUBLIC_BASE_URL } from '$env/static/public';
export const ssr = false;

export async function load() {
	// const res = await fetch(`${PUBLIC_BASE_URL}/user`, {
	// 	credentials: 'include'
	// });
	// let user = null;
	// try {
	// 	if (res.ok) {
	// 		user = await res.json();
	// 	}
	// }
	// catch (err) {
	// 	user = null;
	// }

	// return { user: user };
}