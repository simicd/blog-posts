# How To Write a Custom useFetch Hook For API Calls (part I)
# A walk-through with React’s useState, useEffect and useCallback

In modern web applications, data and functionality is frequently accessible through REST APIs. As simple as it sounds, sending requests turns quite quickly from one line of code to dozens of lines:

1. Call API endpoint using the fetch() function
2. Check for response status code (e.g. 200 = Success, 404 = Not found, …)
3. Extract json body from response
4. Catch potential errors in a try/catch block
5. Put all of this in an useEffect hook (and work around the fact that useEffect only takes synchronous functions while fetch is an asynchronous one…)

As you can imagine, it requires some effort to apply all these steps consistently. Sometimes I omitted catching the error, other times forgot checking the response code before extracting, etc. So I set out to write a custom hook performing all these steps. There were several challenges on the way. Finding solutions taught me a lot about hooks. With this blog post, I want to share both the problems I encountered as well as how to solve them.

[https://cdn-images-1.medium.com/max/2600/0*el6CwKbutZMnxX46](https://cdn-images-1.medium.com/max/2600/0*el6CwKbutZMnxX46)

Photo by [Jannes Glas](https://unsplash.com/@jannesglas?utm_source=medium&utm_medium=referral) on [Unsplash](https://unsplash.com/?utm_source=medium&utm_medium=referral)

## Starting point

Before I started extracting the functionality into a hook, code similar to this was repeated in several components:

<script src="https://gist.github.com/simicd/563e39235f241c48ebc6c4debe2d2af5.js"></script>

I’ll use this example throughout the blog post and explain the purpose of the individual blocks (familiarity with state hook, effect hook and React in general are expected). Since the API is open to anyone, you can follow along and replicate each step. The component will return a random image from the fantastic [Dog API](https://dog.ceo/dog-api/) 🐶:

![https://cdn-images-1.medium.com/max/1263/1*Zu0OBqTi_3-Kvf_WFXSa_Q.png](https://cdn-images-1.medium.com/max/1263/1*Zu0OBqTi_3-Kvf_WFXSa_Q.png)

Note that I’m using TypeScript — if you prefer JavaScript strip away the type definitions (e.g. `string`, `interface` blocks, …). For your convenience, the final hook is stored [here in TypeScript](https://gist.github.com/simicd/02ce79612d0971441b33b7c816930d8e) and [JavaScript](https://gist.github.com/simicd/bbf37fe119c7b344634e4d47d2709fea).

## Step 1: Define a custom hook

The first step is to create a new file (e.g. `useFetch.ts`) and define a function that accepts URL and request parameters as inputs. By convention, hooks are prefixed with *use:*

<script src="https://gist.github.com/simicd/219be594b9e3f77b049d5f86e44dce6a.js"></script>

A few things to note here:

- `RequestProps` interface represents all inputs of the hook. `RequestInfo` and `RequestInit` are types defined by the `fetch()` function
- `DogImageType` is the type returned by the API (in this case a message with the image url and the status message)
- The custom hook uses a state hook — updating the state will re-render the caller component
- The useEffect hook is meant for side-effects, i.e. interactions with functionality outside of the React component. Examples are saving to browser local storage or calling an API.
- Within the effect hook the `fetch()` function submits an API request. If successful (status code 200), the data is passed to the state setter; else an error is printed in the console.
- The hook runs only once since the second parameter is an empty array

If you run the code above you will run into an error. useEffect does not accept asynchronous functions!

![https://cdn-images-1.medium.com/max/1263/1*ValbxncMNjMxQEjasOr2eA.png](https://cdn-images-1.medium.com/max/1263/1*ValbxncMNjMxQEjasOr2eA.png)

The well-accepted workaround: Define the async function within a synchronous one and call it immediately:

<script src="https://gist.github.com/simicd/3fa8d95a74a5ee12e852383d384da50d.js"></script>

The custom hook should work now & can be called in the component. Much cleaner!

<script src="https://gist.github.com/simicd/e8249fdfe18bf57212aff25672134092.js"></script>

### Specify dependencies

First issue resolved — but the next one awaits already. The compiler will return a warning: `url` and `init` have to be specified as dependencies.

![https://cdn-images-1.medium.com/max/1263/1*4W6EDZtSUm1yk49JzQqWZA.png](https://cdn-images-1.medium.com/max/1263/1*4W6EDZtSUm1yk49JzQqWZA.png)

Why is that? The `fetch()` function in the effect hook depends on these two parameters. However, they are not created within the scope of the hook. With an empty array, it will run once when component is initialized and then never again. But what if `url` or `init` change?

This could become a potential source of bugs. Clearly, if any of the two parameters change, we want the hook to re-run. Therefore both should be added to the array `[url, init]`:

<script src="https://gist.github.com/simicd/0154eea4334ccaba00802fd4d780ab3e.js"></script>

### Objects as dependencies

All good? Not really…

When I called the hook using the following example, the hook was called again, and again, and again… Before I noticed, I ended up with 20'000 calls in a few minutes. Why? Neither `url` nor `init` changed?!

<script src="https://gist.github.com/simicd/1199f2deb9c717a667cf20cf51f37d30.js"></script>

With trial and error I figured out:

- Primitive types (string, number, boolean) as dependency variables — no problem
- Objects in the dependency array — infinite loop (even with empty objects `{}`)

useEffect seems not to perform a content check for objects. Instead it treats each object as new instance — even when it has the same content. In the example above `init: {}` caused the issue. Potential solutions:

- Explicitly check for individual keys of the object (e.g. `init.headers`, `init.body`, ...). There is a dozen of keys and some of them are objects themselves. Won’t work.

    ![https://cdn-images-1.medium.com/max/1263/1*QMnWicYTVpifCcKv--joHg.png](https://cdn-images-1.medium.com/max/1263/1*QMnWicYTVpifCcKv--joHg.png)

- Use `Object.values(init)` to extract all values of an object. This is better than the previous option since one wouldn't need to type out all keys of `init`. But again, not all values of `init` are primitive types. This would still result in an infinite loop.

Work-around: Stringify objects with `JSON.stringify(init)`. If the object doesn't change, stringify will produce the same string and no re-run occurs.

<script src="https://gist.github.com/simicd/dfe42d237348ea718673103de6bcad21.js"></script>

### No complex evaluations

Next problem: The linter spits out a warning that complex evaluations are not allowed in the dependency list.

![https://cdn-images-1.medium.com/max/1263/1*zTVRzavS2FM2_4wYmvrDEA.png](https://cdn-images-1.medium.com/max/1263/1*zTVRzavS2FM2_4wYmvrDEA.png)

By moving the evaluation before the effect hook and storing the two strings as variables, a familiar warning pops up again: `url` and `init` are dependencies and need to be part of the dependency array. Obviously the linter doesn't know that `stringifiedInit` belongs to `init`…

Here I took the conscious decision to silence the warning, knowing that there is a proper dependency check in place. To do so, adding `// eslint-disable-next-line react-hooks/exhaustive-deps` in the line above the dependency list is sufficient to silence the warning.

<script src="https://gist.github.com/simicd/99099ce6b0a0d5e5682adfa1843abcc6.js"></script>

> ❓ If you have a suggestion for an alternative way of resolving this I would highly appreciate your input

## Step 2: Optional callback function to process response

Often, the API response has to be processed before it can be displayed to the user. So I wanted to have a possibility to pass a function (here called `processData`) which takes the json body and reshapes it into the desired format.

Since the callback function is optional, it could be undefined. In this case a simple arrow function will take the json body and just cast the type.

`const processJson = processData || ((jsonBody: any) => jsonBody as DogImageType);`

Here the full code so far:

<script src="https://gist.github.com/simicd/16d416399c888d31b5d7fc9756c2da0d.js"></script>

… and again an infinite loop!

<script src="https://gist.github.com/simicd/abedb98016d887e0800d63303fc5cb1c.js"></script>

Reason: Now the initialization of the arrow function is creating a new instance on every render. The useEffect hook believes the dependency has changed and that it should be executed again.

Luckily, React provides a nice recipe for that: the **useCallback** hook. This hook takes a function as input and returns the same function as output. Only difference: The returned function is cached.

Similar to the effect hook, the callback hook has a dependency array as second parameter. If an empty array is provided, the function will only be declared once by React — exactly what we need!

<script src="https://gist.github.com/simicd/b9b80b8f8088fb3fbb62f7055de717f2.js"></script>

## Step 3: Generic type

Finally, the hook works without infinite loops and without warnings! However, if the hook is supposed to be broadly applicable, the return type can be any shape of data. Right now, the hook will always return an object of `DogImageType` (i.e. with a message field and status field).

The solution: [generic types](https://www.typescriptlang.org/docs/handbook/generics.html). **Generics** is a concept that exists in many typed programming languages. In a nutshell, it allows replacing a concrete type (e.g. `DogImageType`) with a placeholder type (typically denoted with `T`). The placeholder is filled with a concrete type when the function is eventually called.

How to turn the hook into a generic one?

- In the interface append a `<T>` after the interface name → generic interface
- In the function declaration prepend the parameter bracket section with `<T>(...)` → generic function
- Replace any `DogImageType` within the function or interface with `T` (e.g. `useState<DogImageType>()` → `useState<T>()`)

    <script src="https://gist.github.com/simicd/52261f5c32a828e389257d23bf75e006.js"></script>

- Finally, when calling the function, pass the concrete type (e.g. `useFetch<DogImageType>(...)`). Under the hood, the fetch hook will now replace `T` with `DogImageType` and return the data as `DogImageType`

    <script src="https://gist.github.com/simicd/eb96a960b25eff9015c5a33396a98a74.js"></script>

With this, the useFetch hook now takes any parameters the `fetch(...)` function would take, too. It’s able to process data with a callback and the best part: Calling an API requires only one line of code!

## Summary 📝

> 📦 You can find the complete [TypeScript code here](https://gist.github.com/simicd/02ce79612d0971441b33b7c816930d8e). For the [JavaScript version see the link here](https://gist.github.com/simicd/bbf37fe119c7b344634e4d47d2709fea)

A summary of the hooks used in t his post and the challenges:

### Recap built-in hooks

- useState: The state hook stores information and triggers a re-render when he setter function is called to update that information.
- useEffect: Whenever a React component is interacting with functionality that is outside the component (so-called side-effect), an effect hook should be used. Examples: Calling an API. Reading file from disk.
- useCallback: If you have functions defined in a component, React will initialize them on every re-render. Usually that’s negligible performance-wise. In case the declaration itself is costly, the callback hook will cache the function and on subsequent renders re-use it.

### **Problems & solutions 💡**

- Object as dependency parameter in effect hook causing infinite loop  → Turn into string with `JSON.stringfiy`
- Function as dependency parameter in effect hook causing infinite loop → Use callback hook to instantiate function only once
- Generalize function return type→ Use [generics](https://www.typescriptlang.org/docs/handbook/generics.html) to replace a concrete type with a placeholder type

## Next steps 🚀

The hook runs successfully if the API request takes place at initialization. But what if you would like to send a request on button click (or any other event)? This topic will be covered in the next blog post!

## Follow me on Twitter 🌠

I’m regularly sharing tips about Python, React & Azure Cloud — if you are interested I’d be happy to [meet you on Twitter](https://twitter.com/simicdds) ✨

## Run at initialization works! But what about on event?

By jumping through all the hoops I had now a hook that worked at initialization. I was able to call it like this:

[CODE]

Works! Happily I tried to refactor one of the components that submitted a put request. Can you see the problem?

Hooks must follow the same order on every render and must be deterministic - putting them into a function violates this principle. Back to the whiteboard.

A custom hook builds on top of existing React hooks and is therefore subject to [the same rules as built-in hooks](https://reactjs.org/docs/hooks-rules.html).