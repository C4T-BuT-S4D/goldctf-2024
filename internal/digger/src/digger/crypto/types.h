#pragma once

#include <array>
#include <vector>

namespace Digger::Crypto {

    using Bit = bool;
    using Byte = uint8_t;

    using Bits = std::vector<Bit>;
    using Bytes = std::vector<Byte>;

    template <size_t Size>
    using Table = std::array<size_t, Size>;

    template <size_t Size>
    using Mapping = std::vector<Table<Size>>;

}; /* namespace Digger::Crypto */
