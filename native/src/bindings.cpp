// NewsKoo C++ acceleration (pybind11).
//
// Phase-0 skeleton: correct, compilable implementations of the hot-path
// primitives the Python facade (newskoo.core.accel) expects. Phase 4 hardens
// these (ICU-based Unicode normalization, SIMD popcount, windowed aggregation).
//
// Exposed API (must match newskoo/core/accel.py semantics):
//   normalize(str) -> str        : lowercase + whitespace-collapse (UTF-8 safe)
//   simhash64(str) -> uint64      : 64-bit SimHash over whitespace tokens
//   hamming(uint64,uint64) -> int : Hamming distance

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <string>
#include <vector>

namespace py = pybind11;

// ASCII-lowercase + collapse runs of ASCII whitespace to a single space.
// Non-ASCII bytes (UTF-8 multibyte) pass through untouched.
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
    for (unsigned char c : norm) {
        const bool alnum = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c >= 0x80;
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

static uint64_t simhash64(const std::string &text) {
    const std::string norm = normalize(text);
    int counts[64] = {0};
    for (const auto &tok : tokenize(norm)) {
        const uint64_t h = fnv1a(tok);
        for (int i = 0; i < 64; ++i) counts[i] += ((h >> i) & 1ULL) ? 1 : -1;
    }
    uint64_t out = 0;
    for (int i = 0; i < 64; ++i)
        if (counts[i] > 0) out |= (1ULL << i);
    return out;
}

static int hamming(uint64_t a, uint64_t b) {
    return __builtin_popcountll(a ^ b);
}

PYBIND11_MODULE(newskoo_native, m) {
    m.doc() = "NewsKoo C++ acceleration";
    m.def("normalize", &normalize, py::arg("text"));
    m.def("simhash64", &simhash64, py::arg("text"));
    m.def("hamming", &hamming, py::arg("a"), py::arg("b"));
}
