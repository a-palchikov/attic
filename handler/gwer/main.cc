
#include <windows.h>

#define DDK_BUILD

#if !defined(DDK_BUILD)
#include <werapi.h>
#endif

#if defined(GWER_EXPORTS)
#define GWER_API __declspec(dllexport)
#else
#define GWER_API 
#endif

#if defined(__cplusplus)
extern "C" {
#endif

#if defined(DDK_BUILD)
typedef struct _WER_RUNTIME_EXCEPTION_INFORMATION
{
    DWORD dwSize;
    HANDLE hProcess;
    HANDLE hThread;
    EXCEPTION_RECORD exceptionRecord;
    CONTEXT context;
    PCWSTR pwszReportId;
} WER_RUNTIME_EXCEPTION_INFORMATION, *PWER_RUNTIME_EXCEPTION_INFORMATION;
#endif

	HRESULT GWER_API WINAPI OutOfProcessExceptionEventCallback(
	  __in     PVOID pContext,
	  __in     const PWER_RUNTIME_EXCEPTION_INFORMATION pExceptionInformation,
	  __out    BOOL *pbOwnershipClaimed,
	  __out    PWSTR pwszEventName,
	  __inout  PDWORD pchSize,
	  __out    PDWORD pdwSignatureCount
	) {
		pContext, pExceptionInformation;
		// todo
		*pbOwnershipClaimed = TRUE;
		LPCWSTR eventName = L"SampleCrashEvent";
		wcsncpy_s(pwszEventName, MAX_PATH,  eventName, wcslen(eventName));
		*pchSize = wcslen(eventName);
		*pdwSignatureCount = 0;
		::MessageBoxW(NULL, L"WTF??!", L"Title (wtf)", MB_OKCANCEL);
		return S_OK;
	}
	HRESULT GWER_API WINAPI OutOfProcessExceptionEventSignatureCallback(
	  __in     PVOID pContext,
	  __in     const PWER_RUNTIME_EXCEPTION_INFORMATION pExceptionInformation,
	  __in     DWORD dwIndex,
	  __out    PWSTR pwszName,
	  __inout  PDWORD pchName,
	  __out    PWSTR pwszValue,
	  __inout  PDWORD pchValue
	) {
		pContext, pExceptionInformation, dwIndex, pwszName, pchName, pwszValue, pchValue;
		// todo
		// we don't return shit here
		return S_OK;
	}
	HRESULT GWER_API WINAPI OutOfProcessExceptionEventDebuggerLaunchCallback(
	  __in     PVOID pContext,
	  __in     const PWER_RUNTIME_EXCEPTION_INFORMATION pExceptionInformation,
	  __out    PBOOL pbIsCustomDebugger,
	  __out    PWSTR pwszDebuggerLaunch,
	  __inout  PDWORD pchDebuggerLaunch,
	  __out    PBOOL pbIsDebuggerAutolaunch
	) {
		pContext, pExceptionInformation, pchDebuggerLaunch;
		// todo
		*pbIsCustomDebugger = TRUE;
		LPCWSTR dbgrPath = L"d:\\Programs\\Windbg\\Windbg.exe -p %ld -e %ld";
		wcsncpy_s(pwszDebuggerLaunch, MAX_PATH, dbgrPath, wcslen(dbgrPath));
		*pbIsDebuggerAutolaunch = TRUE;
		return S_OK;
	}
#if defined(__cplusplus)
}
#endif
