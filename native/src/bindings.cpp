// NewsKoo C++ acceleration (pybind11).
//
// Correct, compilable implementations of the hot-path primitives the Python
// facade (newskoo.core.accel) expects. Semantics must match the pure-Python
// fallbacks in accel.py so behaviour is identical whether or not this module
// is built.
//
// Exposed API:
//   normalize(str) -> str            : lowercase + whitespace-collapse (UTF-8 safe)
//   simhash64(str) -> uint64         : 64-bit SimHash over whitespace tokens
//   simhash_tokens(list[str]) -> int : 64-bit SimHash over caller-supplied tokens
//   hamming(uint64,uint64) -> int    : Hamming distance
//   hamming_table(int, list[int]) -> list[int]
//                                    : distances from one hash to many (batched)
//   nearest(int, list[int]) -> (idx, dist)
//                                    : index + distance of the closest hash

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace py = pybind11;

// ASCII-lowercase + collapse runs of ASCII whitespace to a single space.
// Non-ASCII bytes (UTF-8 multibyte) pass through untouched so multilingual
// text is preserved byte-for-byte.
static std::string normalize(const std::string &in) {
    std::string out;
    out.reserve(in.size());
    bool in_ws = false;
    bool started = false;
    for (unsigned char c : in) {
        const bool ws = (c == ' ' || c == '\t' || c == '\n' || c == '\r' ||
                         c == '\f' || c == '\v');
        if (ws) {
            in_ws = true;
            continue;
        }
        if (in_ws && started) out.push_back(' ');
        in_ws = false;
        started = true;
        if (c >= 'A' && c <= 'Z') c = static_cast<unsigned char>(c - 'A' + 'a');
        out.push_back(static_cast<char>(c));
    }
    return out;
}

// FNV-1a 64-bit hash of a token.
static inline uint64_t fnv1a(const std::string &s) {
    uint64_t h = 1469598103934665603ULL;
    for (unsigned char c : s) {
        h ^= c;
        h *= 1099511628211ULL;
    }
    return h;
}

static std::vector<std::string> tokenize(const std::string &norm) {
    std::vector<std::string> toks;
    std::string cur;
    cur.reserve(32);
    for (unsigned char c : norm) {
        const bool alnum =
            (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c >= 0x80;
        if (alnum) {
            cur.push_back(static_cast<char>(c));
        } else if (!cur.empty()) {
            toks.push_back(cur);
            cur.clear();
        }
    }
    if (!cur.empty()) toks.push_back(cur);
    return toks;
}

// Fold a sequence of token hashes into a 64-bit simhash.
static inline uint64_t simhash_from_hashes(const std::vector<uint64_t> &hashes) {
    int counts[64] = {0};
    for (const uint64_t h : hashes) {
        for (int i = 0; i < 64; ++i) counts[i] += ((h >> i) & 1ULL) ? 1 : -1;
    }
    uint64_t out = 0;
    for (int i = 0; i < 64; ++i)
        if (counts[i] > 0) out |= (1ULL << i);
    return out;
}

static uint64_t simhash64(const std::string &text) {
    const std::string norm = normalize(text);
    const std::vector<std::string> toks = tokenize(norm);
    std::vector<uint64_t> hashes;
    hashes.reserve(toks.size());
    for (const auto &tok : toks) hashes.push_back(fnv1a(tok));
    return simhash_from_hashes(hashes);
}

// SimHash over caller-supplied tokens. Each token is normalized the same way
// the string path tokenizes (lowercase + non-ASCII kept) so results line up
// with simhash64 when given equivalent tokens.
static uint64_t simhash_tokens(const std::vector<std::string> &tokens) {
    std::vector<uint64_t> hashes;
    hashes.reserve(tokens.size());
    for (const auto &tok : tokens) {
        const std::string norm = normalize(tok);
        for (const auto &piece : tokenize(norm)) hashes.push_back(fnv1a(piece));
    }
    return simhash_from_hashes(hashes);
}

static inline int hamming(uint64_t a, uint64_t b) {
    return __builtin_popcountll(a ^ b);
}

// Distances from one query hash to every hash in `others` (batched popcount).
static std::vector<int> hamming_table(uint64_t query,
                                      const std::vector<uint64_t> &others) {
    std::vector<int> out;
    out.reserve(others.size());
    for (const uint64_t h : others)
        out.push_back(__builtin_popcountll(query ^ h));
    return out;
}

// Index + distance of the closest hash in `others`; (-1, 64) if empty.
static std::pair<int, int> nearest(uint64_t query,
                                   const std::vector<uint64_t> &others) {
    int best_idx = -1;
    int best_dist = std::numeric_limits<int>::max();
    for (size_t i = 0; i < others.size(); ++i) {
        const int d = __builtin_popcountll(query ^ others[i]);
        if (d < best_dist) {
            best_dist = d;
            best_idx = static_cast<int>(i);
            if (d == 0) break;  // exact match: cannot do better
        }
    }
    if (best_idx < 0) return {-1, 64};
    return {best_idx, best_dist};
}

PYBIND11_MODULE(newskoo_native, m) {
    m.doc() = "NewsKoo C++ acceleration (simhash, normalization, dedup helpers)";
    m.def("normalize", &normalize, py::arg("text"),
          "Lowercase + whitespace-collapse, UTF-8 byte-safe.");
    m.def("simhash64", &simhash64, py::arg("text"),
          "64-bit SimHash over whitespace/alnum tokens.");
    m.def("simhash_tokens", &simhash_tokens, py::arg("tokens"),
          "64-bit SimHash over caller-supplied tokens.");
    m.def("hamming", &hamming, py::arg("a"), py::arg("b"),
          "Hamming distance between two 64-bit hashes.");
    m.def("hamming_table", &hamming_table, py::arg("query"), py::arg("others"),
          "Hamming distance from `query` to each hash in `others`.");
    m.def("nearest", &nearest, py::arg("query"), py::arg("others"),
          "(index, distance) of the closest hash in `others`.");
}
