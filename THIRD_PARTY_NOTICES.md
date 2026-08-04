# Third-party notices

Review Radius is licensed under the [MIT License](LICENSE). The licenses listed
here apply to their respective third-party projects and do not change the
license of Review Radius.

## Graphify

The optional tool-routing benchmark invokes
[Graphify](https://github.com/Graphify-Labs/graphify) as the external Python
package [`graphifyy==0.9.32`](https://pypi.org/project/graphifyy/0.9.32/). It is
fetched and run in an isolated temporary environment with `uvx`; Graphify source
code and package artifacts are not vendored in this repository.

Graphify 0.9.32 declares the
[Apache License 2.0](https://github.com/Graphify-Labs/graphify/blob/v0.9.32/LICENSE)
as its package license. Its upstream
[NOTICE](https://github.com/Graphify-Labs/graphify/blob/v0.9.32/NOTICE) credits
Safi Shamsi and the Graphify contributors and notes that portions contributed
before the Apache-2.0 relicensing remain available under the retained
[MIT license](https://github.com/Graphify-Labs/graphify/blob/v0.9.32/LICENSE-MIT).

If Graphify code or package artifacts are later copied into or distributed with
Review Radius, this notice must be reassessed against the exact distributed
version and its license and NOTICE files.
