#pragma once

#include <queue>
#include <unordered_map>

namespace Digger::Primitives {

    template <typename K, typename V>
    class Cache {
    public:
        Cache(size_t size = 8): Size(size) { }
        ~Cache() { }

        Cache(const Cache& other)
            : Size(other.Size)
            , Items(other.Items)
            , Queue(other.Queue) { }

        Cache(Cache&& other)
            : Size(other.Size)
            , Items(std::move(other.Items))
            , Queue(std::move(other.Queue)) { }

        Cache& operator=(const Cache& other) {
            return *this = Cache(other);
        }

        Cache& operator=(Cache&& other) {
            Size = other.Size;
            Items = std::move(other.Items);
            Queue = std::move(other.Queue);

            return *this;
        }

        void Add(const K& key, const V& value) {
            while (Queue.size() >= Size) {
                auto last = Queue.front();
                Queue.pop();

                Items.erase(last);
            }

            if (!Contains(key)) {
                Queue.push(key);
            }

            Items[key] = value;
        }

        const V& Get(const K& key) {
            return Items[key];
        }

        bool Contains(const K& key) const {
            return Items.contains(key);
        }

    private:
        const size_t Size;

        std::unordered_map<K, V> Items;
        std::queue<K> Queue;
    };

}; /* namespace Digger::Primitives */
